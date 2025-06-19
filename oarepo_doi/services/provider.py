import json
import warnings
from collections import ChainMap
from json import JSONDecodeError
import uuid
from invenio_communities import current_communities
from invenio_search.engine import dsl
from datacite.errors import (
    DataCiteNoContentError,
    DataCiteServerError,
)
from invenio_db import db
from invenio_pidstore.providers.base import BaseProvider
import requests
from oarepo_runtime.datastreams.utils import get_record_service_for_record

from marshmallow.exceptions import ValidationError
from flask import current_app

from invenio_pidstore.models import PIDStatus
from invenio_rdm_records.services.pids.providers import DataCiteClient

from invenio_rdm_records.services.pids.providers.base import PIDProvider
from invenio_access.permissions import system_identity
from invenio_pidstore.models import PersistentIdentifier

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
            credentials_def = current_app.config.get("DATACITE_CREDENTIALS")
            credentials = credentials_def.get(slug, None)
            if not credentials:
                credentials = current_app.config.get("DATACITE_CREDENTIALS_DEFAULT", None)
        if credentials is None:
            return None

        return credentials["username"], credentials["password"], credentials["prefix"]

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
        request_metadata, username, password, prefix = self.datacite_request(record, **kwargs)
        request = requests.post(
            url=self.url,
            json=request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
        )
        if request.status_code != 201:
            raise requests.ConnectionError(f"Expected status code 201, but got {request.status_code}")
        content = request.content.decode("utf-8")
        json_content = json.loads(content)
        doi_value = json_content["data"]["id"]
        self.add_doi_value(record, record, doi_value)

        if "event" in kwargs:
            pid_status = 'R'
            parent_doi = self.get_pid_doi_value(record, parent=True)
            if parent_doi is None:

                self.register_parent_doi(record, request_metadata, username, password, prefix)
            elif parent_doi and record.versions.is_latest:
                self.update_parent_doi(record, request_metadata, username, password)
        else:
            pid_status = 'K'

        BaseProvider.create('doi', doi_value, 'rec', record.id, pid_status)
        db.session.commit()

    def register_parent_doi(self, record, request_metadata, username, password, prefix):
        request_metadata["data"]["attributes"]["prefix"] = str(prefix)
        request_metadata["data"]["attributes"]["event"] = "publish"
        request = requests.post(
            url=self.url,
            json=request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
        )
        if request.status_code != 201:
            raise requests.ConnectionError(f"Expected status code 201, but got {request.status_code}")
        content = request.content.decode("utf-8")
        json_content = json.loads(content)
        doi_value = json_content["data"]["id"]
        BaseProvider.create('doi', doi_value, 'rec', record.parent.id, 'R')
        self.add_doi_value(record, record, doi_value, parent=True)
        db.session.commit()

    def update_parent_doi(self, record, request_metadata, username, password):
        url = self.url.rstrip("/") + "/" + self.get_doi_value(record, parent=True).replace("/", "%2F")
        request = requests.put(
            url=url,
            json=request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
        )
        if request.status_code != 200:
            raise requests.ConnectionError(f"Expected status code 200, but got {request.status_code}")

    def update(self, record, url=None, **kwargs):
        doi_value = self.get_doi_value(record)
        if doi_value:
            creds = self.credentials(record)
            if creds is None:
                raise ValidationError(message="No credentials provided.")
            username, password, prefix = creds

            errors = self.metadata_check(record)
            record_service = get_record_service_for_record(record)
            record["links"] = record_service.links_item_tpl.expand(system_identity, record)
            if errors:
                raise ValidationError(message=errors)

            url = self.url.rstrip("/") + "/" + doi_value.replace("/", "%2F")

            request_metadata = {"data": {"type": "dois", "attributes": {}}}
            payload = self.create_datacite_payload(record)
            request_metadata["data"]["attributes"] = payload

            parent_doi = self.get_pid_doi_value(record, parent=True)
            if parent_doi is None and "event" in kwargs:

                self.register_parent_doi(record, request_metadata, username, password, prefix)
            elif parent_doi and record.versions.is_latest:
                self.update_parent_doi(record, request_metadata, username, password)

            if "event" in kwargs:
                request_metadata["data"]["attributes"]["event"] = kwargs["event"]

            request = requests.put(
                url=url,
                json=request_metadata,
                headers={"Content-type": "application/vnd.api+json"},
                auth=(username, password),
            )
            if request.status_code != 200:
                raise requests.ConnectionError(f"Expected status code 200, but got {request.status_code}")

            if "event" in kwargs:
                pid_value = self.get_pid_doi_value(record)
                if hasattr(pid_value, "status") and pid_value.status == "K":
                    pid_value.register()

    def delete(self, record, **kwargs):
        creds = self.credentials(record)
        if creds is None:
            raise ValidationError("No credentials provided.")
        username, password, _ = creds
        doi_value = self.get_doi_value(record)
        url = self.url.rstrip("/") + "/" + doi_value.replace("/", "%2F")
        response = requests.delete(
            url=url,
            headers={"Content-Type": "application/vnd.api+json"},
            auth=(username, password)
        )
        if response.status_code != 204:
            raise requests.ConnectionError(f"Expected status code 204, but got {response.status_code}")
        pid_value = self.get_pid_doi_value(record)
        pid_value.delete()
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
            auth=(username, password)
        )
        if request.status_code != 200:
            raise requests.ConnectionError(f"Expected status code 200, but got {request.status_code}")
        pid_value = self.get_pid_doi_value(record)
        pid_value.delete()
        self.remove_doi_value(record)

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

    def get_doi_value(self, record, parent=False):
        pids = record.parent.get("pids", {}) if parent else record.get("pids", {})
        return pids.get("doi", {}).get("identifier")

    def get_pid_doi_value(self, record, parent=False):
        id = record.parent.id if parent else record.id
        try:
            return PersistentIdentifier.get_by_object('doi', "rec", id)
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
