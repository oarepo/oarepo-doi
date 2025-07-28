import copy
import json
import uuid
from json import JSONDecodeError

import requests
from datacite.errors import DataCiteNoContentError, DataCiteServerError
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_communities import current_communities
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.providers.base import BaseProvider
from invenio_rdm_records.services.pids.providers import DataCiteClient
from invenio_rdm_records.services.pids.providers.base import PIDProvider
from invenio_search.engine import dsl
from marshmallow.exceptions import ValidationError
from oarepo_runtime.datastreams.utils import get_record_service_for_record

from oarepo_doi.settings.models import CommunityDoiSettings


class OarepoDataCitePIDProvider(PIDProvider):
    def __init__(
        self,
        id_,
        client=None,
        serializer=None,
        pid_type="doi",
        default_status=PIDStatus.NEW,
        **kwargs,
    ):
        super().__init__(
            id_,
            client=(client or DataCiteClient("datacite", config_prefix="DATACITE")),
            pid_type=pid_type,
            default_status=default_status,
        )
        self.serializer = serializer

    @property
    def mode(self):
        return current_app.config.get("DATACITE_MODE")

    @property
    def url(self):
        return current_app.config.get("DATACITE_URL")

    @property
    def specified_doi(self):
        return current_app.config.get("DATACITE_SPECIFIED_ID")

    def credentials(self, record):
        slug = self.community_slug_for_credentials(
            record.parent["communities"].get("default", None)
        )
        if not slug:
            credentials = current_app.config.get("DATACITE_CREDENTIALS_DEFAULT", None)
        else:
            doi_settings = (
                db.session.query(CommunityDoiSettings)
                .filter_by(community_slug=slug)
                .first()
            )
            if doi_settings is None:
                credentials = current_app.config.get(
                    "DATACITE_CREDENTIALS_DEFAULT", None
                )
            else:
                credentials = doi_settings
        if credentials is None:
            return None

        return credentials.username, credentials.password, credentials.prefix

    def generate_id(self, record, **kwargs):
        pass  # done at DataCite level

    @classmethod
    def is_enabled(cls, app):
        return True

    def can_modify(self, pid, **kwargs):
        return not pid.is_registered()

    def register(self, pid, record, **kwargs):
        pass

    def create(self, record, **kwargs):
        pass

    def restore(self, pid, **kwargs):
        pass

    def validate(self, record, identifier=None, provider=None, **kwargs):
        return True, []

    def metadata_check(self, record, schema=None, provider=None, **kwargs):
        return []

    def validate_restriction_level(self, record, identifier=None, **kwargs):
        return record["access"]["record"] != "restricted"

    def _log_errors(self, exception):
        ex_txt = exception.args[0] or ""
        if isinstance(exception, DataCiteNoContentError):
            current_app.logger.error(f"No content error: {ex_txt}")
        elif isinstance(exception, DataCiteServerError):
            current_app.logger.error(f"DataCite internal server error: {ex_txt}")
        else:
            try:
                ex_json = json.loads(ex_txt)
            except JSONDecodeError:
                current_app.logger.error(f"Unknown error: {ex_txt}")
                return
            for error in ex_json.get("errors", []):
                reason = error["title"]
                field = error.get("source")
                error_prefix = f"Error in `{field}`: " if field else "Error: "
                current_app.logger.error(f"{error_prefix}{reason}")

    def datacite_request(self, record, **kwargs):
        doi_value = self.get_doi_value(record)
        if doi_value:
            pass

        creds = self.credentials(record)
        if creds is None:
            raise ValidationError(message="No credentials provided.")
        username, password, prefix = creds

        errors = self.metadata_check(record)
        record_service = get_record_service_for_record(record)
        record["links"] = record_service.links_item_tpl.expand(system_identity, record)

        if errors:
            raise ValidationError(message=errors)

        request_metadata = {"data": {"type": "dois", "attributes": {}}}
        payload = self.create_datacite_payload(record)
        request_metadata["data"]["attributes"] = payload

        if self.specified_doi:
            doi = f"{prefix}/{record['id']}"
            request_metadata["data"]["attributes"]["doi"] = doi

        if "event" in kwargs:
            request_metadata["data"]["attributes"]["event"] = kwargs["event"]

        request_metadata["data"]["attributes"]["prefix"] = str(prefix)
        return request_metadata, username, password, prefix

    def create_and_reserve(self, record, **kwargs):
        request_metadata, username, password, prefix = self.datacite_request(
            record, **kwargs
        )
        request = requests.post(
            url=self.url,
            json=request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
        )
        if request.status_code != 201:
            raise requests.ConnectionError(
                f"Expected status code 201, but got {request.status_code}"
            )
        content = request.content.decode("utf-8")
        json_content = json.loads(content)
        doi_value = json_content["data"]["id"]
        self.add_doi_value(record, record, doi_value)
        parent_doi = self.get_pid_doi_value(record, parent=True)

        if "event" in kwargs:
            pid_status = "R"

            if parent_doi is None:

                parent_doi = self.register_parent_doi(
                    record, request_metadata, username, password, prefix, doi_value
                )
            elif parent_doi and record.versions.is_latest:
                self.update_parent_doi(
                    record, request_metadata, username, password, doi_value
                )
        else:
            pid_status = "K"
        if parent_doi and record.is_published:
            self.update_relations(parent_doi, record)

        BaseProvider.create("doi", doi_value, "rec", record.id, pid_status)
        db.session.commit()

    def add_relation(self, identifier, related_identifiers, type):
        if not any(
            item["relatedIdentifier"] == identifier for item in related_identifiers
        ):
            related_identifiers.append(
                {
                    "relationType": type,
                    "relatedIdentifier": identifier,
                    "relatedIdentifierType": "DOI",
                }
            )
            return True
        return False

    def update_relations(self, parent_doi, record):

        creds = self.credentials(record)
        if creds is None:
            raise ValidationError("No credentials provided.")
        username, password, _ = creds
        doi_value = self.get_doi_value(record)
        url = self.url.rstrip("/") + "/" + doi_value.replace("/", "%2F")

        new_data = requests.get(
            url=url,
        )
        new_version_modified_relations_count = 0
        previous_version_modified_relations_count = 0
        if "data" in new_data.json():
            new_related_identifiers = new_data.json()["data"]["attributes"][
                "relatedIdentifiers"
            ]
        else:
            new_related_identifiers = []
        if type(parent_doi) is not str:
            parent_doi = parent_doi.pid_value

        new_version_modified_relations_count += self.add_relation(
            parent_doi, new_related_identifiers, "IsVersionOf"
        )

        previous_version = self.get_previous_version(record)
        if previous_version:
            url = self.url.rstrip("/") + "/" + previous_version.replace("/", "%2F")

            previous_data = requests.get(
                url=url,
            )
            if "data" in previous_data.json():
                previous_related_identifiers = previous_data.json()["data"][
                    "attributes"
                ]["relatedIdentifiers"]
            else:
                previous_related_identifiers = []
            new_version_modified_relations_count += self.add_relation(
                previous_version, new_related_identifiers, "IsNewVersionOf"
            )
            previous_version_modified_relations_count += self.add_relation(
                doi_value, previous_related_identifiers, "IsPreviousVersionOf"
            )
            previous_version_modified_relations_count += self.add_relation(
                parent_doi, previous_related_identifiers, "IsVersionOf"
            )
            if previous_version_modified_relations_count > 0:
                previous_version_request_metadata = {
                    "data": {
                        "type": "dois",
                        "attributes": {
                            "relatedIdentifiers": previous_related_identifiers
                        },
                    }
                }

                request = requests.put(
                    url=url,
                    json=previous_version_request_metadata,
                    headers={"Content-type": "application/vnd.api+json"},
                    auth=(username, password),
                )
                if request.status_code != 200:
                    raise requests.ConnectionError(
                        f"Expected status code 200, but got {request.status_code}"
                    )

        if new_version_modified_relations_count > 0:

            new_version_request_metadata = {
                "data": {
                    "type": "dois",
                    "attributes": {"relatedIdentifiers": new_related_identifiers},
                }
            }
            url = self.url.rstrip("/") + "/" + doi_value.replace("/", "%2F")
            request = requests.put(
                url=url,
                json=new_version_request_metadata,
                headers={"Content-type": "application/vnd.api+json"},
                auth=(username, password),
            )
            if request.status_code != 200:
                raise requests.ConnectionError(
                    f"Expected status code 200, but got {request.status_code}"
                )

    def register_parent_doi(
        self, record, request_metadata, username, password, prefix, rec_doi
    ):
        parent_request_metadata = copy.deepcopy(request_metadata)
        parent_request_metadata["data"]["attributes"]["prefix"] = str(prefix)
        parent_request_metadata["data"]["attributes"]["event"] = "publish"
        related_identifiers = parent_request_metadata["data"]["attributes"].get(
            "relatedIdentifiers", []
        )
        doi_versions = self.get_doi_versions(record)

        if rec_doi not in doi_versions:
            doi_versions.append(rec_doi)
        for doi_version in doi_versions:
            related_identifiers.append(
                {
                    "relationType": "HasVersion",
                    "relatedIdentifier": doi_version,
                    "relatedIdentifierType": "DOI",
                }
            )
        parent_request_metadata["data"]["attributes"][
            "relatedIdentifiers"
        ] = related_identifiers
        request = requests.post(
            url=self.url,
            json=parent_request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
        )
        if request.status_code != 201:
            raise requests.ConnectionError(
                f"Expected status code 201, but got {request.status_code}"
            )

        content = request.content.decode("utf-8")
        json_content = json.loads(content)
        doi_value = json_content["data"]["id"]
        BaseProvider.create("doi", doi_value, "rec", record.parent.id, "R")
        self.add_doi_value(record, record, doi_value, parent=True)
        db.session.commit()
        return doi_value

    def update_parent_doi(self, record, request_metadata, username, password, rec_doi):
        parent_request_metadata = copy.deepcopy(request_metadata)
        doi_versions = self.get_doi_versions(record)
        if rec_doi not in doi_versions:
            doi_versions.append(rec_doi)
        related_identifiers = parent_request_metadata["data"]["attributes"].get(
            "relatedIdentifiers", []
        )
        for doi_version in doi_versions:
            related_identifiers.append(
                {
                    "relationType": "HasVersion",
                    "relatedIdentifier": doi_version,
                    "relatedIdentifierType": "DOI",
                }
            )
        parent_request_metadata["data"]["attributes"][
            "relatedIdentifiers"
        ] = related_identifiers

        url = (
            self.url.rstrip("/")
            + "/"
            + self.get_doi_value(record, parent=True).replace("/", "%2F")
        )
        request = requests.put(
            url=url,
            json=parent_request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
        )
        if request.status_code != 200:
            raise requests.ConnectionError(
                f"Expected status code 200, but got {request.status_code}"
            )

    def update(self, record, url=None, **kwargs):
        doi_value = self.get_doi_value(record)
        if doi_value:
            creds = self.credentials(record)
            if creds is None:
                raise ValidationError(message="No credentials provided.")
            username, password, prefix = creds

            errors = self.metadata_check(record)
            record_service = get_record_service_for_record(record)
            record["links"] = record_service.links_item_tpl.expand(
                system_identity, record
            )
            if errors:
                raise ValidationError(message=errors)

            url = self.url.rstrip("/") + "/" + doi_value.replace("/", "%2F")

            request_metadata = {"data": {"type": "dois", "attributes": {}}}
            payload = self.create_datacite_payload(record)
            request_metadata["data"]["attributes"] = payload

            parent_doi = self.get_pid_doi_value(record, parent=True)

            if parent_doi is None and "event" in kwargs:

                parent_doi = self.register_parent_doi(
                    record, request_metadata, username, password, prefix, doi_value
                )
            elif parent_doi and record.versions.is_latest:
                self.update_parent_doi(
                    record, request_metadata, username, password, doi_value
                )
            related_identifiers = request_metadata["data"]["attributes"].get(
                "relatedIdentifiers", []
            )

            if "event" in kwargs:
                request_metadata["data"]["attributes"]["event"] = kwargs["event"]

            request_metadata["data"]["attributes"][
                "relatedIdentifiers"
            ] = related_identifiers

            request = requests.put(
                url=url,
                json=request_metadata,
                headers={"Content-type": "application/vnd.api+json"},
                auth=(username, password),
            )
            if request.status_code != 200:
                raise requests.ConnectionError(
                    f"Expected status code 200, but got {request.status_code}"
                )

            if "event" in kwargs:
                pid_value = self.get_pid_doi_value(record)
                if hasattr(pid_value, "status") and pid_value.status == "K":
                    pid_value.register()
            if parent_doi and record.is_published:
                self.update_relations(parent_doi, record)

    def delete_draft(self, record, **kwargs):
        creds = self.credentials(record)
        if creds is None:
            raise ValidationError("No credentials provided.")
        username, password, _ = creds
        doi_value = self.get_doi_value(record)
        url = self.url.rstrip("/") + "/" + doi_value.replace("/", "%2F")
        response = requests.delete(
            url=url,
            headers={"Content-Type": "application/vnd.api+json"},
            auth=(username, password),
        )
        if response.status_code != 204:
            raise requests.ConnectionError(
                f"Expected status code 204, but got {response.status_code}"
            )
        pid_value = self.get_pid_doi_value(record)
        pid_value.delete()
        pid_value.unassign()
        self.remove_doi_value(record)

    def delete_published(self, record, **kwargs):
        creds = self.credentials(record)
        if creds is None:
            raise ValidationError("No credentials provided.")
        username, password, _ = creds
        doi_value = self.get_doi_value(record)
        url = self.url.rstrip("/") + "/" + doi_value.replace("/", "%2F")
        request_metadata = {"data": {"type": "dois", "attributes": {"event": "hide"}}}
        request = requests.put(
            url=url,
            json=request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
        )
        if request.status_code != 200:
            raise requests.ConnectionError(
                f"Expected status code 200, but got {request.status_code}"
            )
        pid_value = self.get_pid_doi_value(record)
        pid_value.delete()

    def create_datacite_payload(self, data):
        pass

    def community_slug_for_credentials(self, value):
        if not value:
            return None
        try:
            uuid.UUID(value, version=4)
            search = current_communities.service._search(
                "search",
                system_identity,
                {},
                None,
                extra_filter=dsl.Q("term", **{"id": value}),
            )
            community = search.execute()
            c = list(community.hits.hits)[0]
            return c._source.slug
        except:
            return value

    def get_versions(self, record):
        topic_service = get_record_service_for_record(record)
        versions = topic_service.search_versions(
            identity=system_identity, id_=record.pid.pid_value, params={"size": 1000}
        )
        versions_hits = versions.to_dict()["hits"]["hits"]
        return versions_hits

    def get_previous_version(self, record):
        versions_hits = self.get_versions(record)
        for version in versions_hits:
            if "versions" not in version or "pids" not in version:
                continue
            is_latest = version["versions"].get("is_latest")
            is_published = version["is_published"]
            doi = version["pids"].get("doi")

            if is_latest and is_published and doi:
                return doi["identifier"]

        return None

    def get_doi_versions(self, record):
        versions_hits = self.get_versions(record)
        doi_versions = []
        for version in versions_hits:
            pids = version.get("pids", {})
            if (
                "doi" in pids
                and "provider" in pids["doi"]
                and pids["doi"]["provider"] == "datacite"
            ):
                doi_versions.append(pids["doi"]["identifier"])
        return doi_versions

    def get_doi_value(self, record, parent=False):
        pids = record.parent.get("pids", {}) if parent else record.get("pids", {})
        return pids.get("doi", {}).get("identifier")

    def get_pid_doi_value(self, record, parent=False):
        id = record.parent.id if parent else record.id
        try:
            return PersistentIdentifier.get_by_object("doi", "rec", id)
        except:
            return None

    def add_doi_value(self, record, data, doi_value, parent=False):
        pids = record.parent.get("pids", {}) if parent else record.get("pids", {})
        pids["doi"] = {"provider": "datacite", "identifier": doi_value}
        if parent:
            data.parent.pids = pids
            record.update(data)
            record.parent.commit()
        else:
            data.pids = pids
            record.update(data)
            record.commit()

    def remove_doi_value(self, record):
        pids = record.get("pids", {})
        if "doi" in pids:
            pids.pop("doi")
        record.commit()
