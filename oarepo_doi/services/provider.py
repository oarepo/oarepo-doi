#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI oarepo provider."""

from __future__ import annotations

import copy
import json
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, cast, override

import requests  # type: ignore[import-untyped]
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_communities import current_communities
from invenio_db import db
from invenio_pidstore.errors import PersistentIdentifierError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.providers.base import BaseProvider
from invenio_rdm_records.services.pids.providers import DataCiteClient
from invenio_rdm_records.services.pids.providers.base import PIDProvider
from invenio_search.engine import dsl
from marshmallow.exceptions import ValidationError
from oarepo_runtime.datastreams.utils import get_record_service_for_record

from oarepo_doi.settings.models import CommunityDoiSettings

if TYPE_CHECKING:
    from invenio_records.api import Record


class OarepoDataCitePIDProvider(PIDProvider):
    """Oarepo DOI provider."""

    def __init__(
        self,
        id_: str,
        client: DataCiteClient | None = None,
        serializer: Any | None = None,
        pid_type: str = "doi",
        default_status: PIDStatus = PIDStatus.NEW,
    ):
        """Construct."""
        super().__init__(
            id_,
            client=(client or DataCiteClient("datacite", config_prefix="DATACITE")),
            pid_type=pid_type,
            default_status=default_status,
        )
        self.serializer = serializer

    @property
    def mode(self) -> Any:
        """Return DOI mode."""
        return current_app.config.get("DATACITE_MODE")

    @property
    def url(self) -> Any:
        """Return datacite url."""
        return current_app.config.get("DATACITE_URL")

    @property
    def specified_doi(self) -> Any:
        """Check if DOI should be manually provided."""
        return current_app.config.get("DATACITE_SPECIFIED_ID")

    def credentials(self, record: Any) -> tuple[str, str, str] | None:
        """Return credentials."""
        slug = self.community_slug_for_credentials(record.parent["communities"].get("default", None))
        if not slug:
            credentials = current_app.config.get("DATACITE_CREDENTIALS_DEFAULT", None)
        else:
            doi_settings = db.session.query(CommunityDoiSettings).filter_by(community_slug=slug).first()
            if doi_settings is None:
                credentials = current_app.config.get("DATACITE_CREDENTIALS_DEFAULT", None)
            else:
                credentials = doi_settings
        if credentials is None:
            return None

        return credentials.username, credentials.password, credentials.prefix

    @override
    def generate_id(self, record: Any, **kwargs: Any) -> None:
        """Mute invenio method."""
        # done at DataCite level

    @classmethod
    @override
    def is_enabled(cls) -> Any:
        """Check if is enabled."""
        return True

    def can_modify(self, pid: PersistentIdentifier, **kwargs: Any) -> Any:
        """Check if can be modified."""
        _ = kwargs
        return not pid.is_registered()

    def register(self, pid: Any, **kwargs: Any) -> Any:
        """Mute invenio method."""

    def create(self, record: Any, pid_value: str | None = None, status: str | None = None, **kwargs: Any) -> Any:
        """Mute invenio method."""

    def restore(self, pid: Any, **kwargs: Any) -> Any:
        """Mute invenio method."""

    @override
    def validate(
        self, record: Record, identifier: str | None = None, provider: PIDProvider | None = None, **kwargs: Any
    ) -> Any:
        """Validate metadata."""
        return True, []

    def metadata_check(
        self, record: Record, schema: Any | None = None, provider: PIDProvider | None = None, **kwargs: Any
    ) -> list:
        """Check metadata against schema."""
        _, _, _, _ = record, schema, provider, kwargs

        return []

    @override
    def validate_restriction_level(self, record: Record, identifier: str | None = None, **kwargs: Any) -> Any:
        """Check if record not restricted."""
        return record["access"]["record"] != "restricted"

    def datacite_request(self, record: Record, **kwargs: Any) -> Any:
        """Create Datacite request."""
        doi_value = self.get_doi_value(record)
        if doi_value:
            pass

        creds = self.credentials(record)
        if creds is None:
            raise ValidationError(message="No credentials provided.")
        username, password, prefix = creds

        errors = self.metadata_check(record)
        record_service = get_record_service_for_record(record)
        if record_service is not None and hasattr(record_service, "links_item_tpl"):
            record["links"] = record_service.links_item_tpl.expand(system_identity, record)

            if errors:
                raise ValidationError(message=errors)

            request_metadata: dict[str, Any] = {"data": {"type": "dois", "attributes": {}}}
            payload = self.create_datacite_payload(record)
            request_metadata["data"]["attributes"] = payload

            if self.specified_doi:
                doi = f"{prefix}/{record['id']}"
                request_metadata["data"]["attributes"]["doi"] = doi

            if "event" in kwargs:
                request_metadata["data"]["attributes"]["event"] = kwargs["event"]

            request_metadata["data"]["attributes"]["prefix"] = str(prefix)
            return request_metadata, username, password, prefix
        return None

    def create_and_reserve(self, record: Any, **kwargs: Any) -> None:
        """Create DOI and reserve it on the Datacite."""
        request_metadata, username, password, prefix = self.datacite_request(record, **kwargs)
        request = requests.post(
            url=self.url,
            json=request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
            timeout=20,
        )
        if request.status_code != HTTPStatus.CREATED:
            raise requests.ConnectionError(f"Expected status code {HTTPStatus.CREATED}, but got {request.status_code}")
        content = request.content.decode("utf-8")
        json_content = json.loads(content)
        doi_value = json_content["data"]["id"]
        self.add_doi_value(record, record, doi_value)
        parent_doi = self.get_pid_doi_value(record, parent=True)

        if "event" in kwargs:
            pid_status = "R"

            if parent_doi is None:
                parent_doi = self.register_parent_doi(record, request_metadata, (username, password, prefix), doi_value)
            elif parent_doi and record.versions.is_latest:
                self.update_parent_doi(record, request_metadata, username, password, doi_value)
        else:
            pid_status = "K"
        if parent_doi and record.is_published:
            self.update_relations(parent_doi, record)

        BaseProvider.create("doi", doi_value, "rec", record.id, pid_status)
        db.session.commit()

    def add_relation(self, identifier: PersistentIdentifier, related_identifiers: list, _type: str) -> bool:
        """Add relation for the DOIs."""
        if not any(item["relatedIdentifier"] == identifier for item in related_identifiers):
            related_identifiers.append(
                {
                    "relationType": _type,
                    "relatedIdentifier": identifier,
                    "relatedIdentifierType": "DOI",
                }
            )
            return True
        return False

    def update_relations(self, parent_doi: PersistentIdentifier, record: Record) -> None:
        """Update DOI relations."""
        creds = self.credentials(record)
        if creds is None:
            raise ValidationError("No credentials provided.")
        username, password, _ = creds
        doi_value = self.get_doi_value(record)
        url = self.url.rstrip("/") + "/" + doi_value.replace("/", "%2F")

        new_data = requests.get(
            url=url,
            timeout=20,
        )
        new_version_modified_relations_count = 0
        previous_version_modified_relations_count = 0
        if "data" in new_data.json():
            new_related_identifiers = new_data.json()["data"]["attributes"]["relatedIdentifiers"]
        else:
            new_related_identifiers = []
        if type(parent_doi) is not str:
            parent_doi = parent_doi.pid_value

        new_version_modified_relations_count += self.add_relation(parent_doi, new_related_identifiers, "IsVersionOf")

        previous_version = self.get_previous_version(record)
        if previous_version:
            url = self.url.rstrip("/") + "/" + previous_version.replace("/", "%2F")

            previous_data = requests.get(
                url=url,
                timeout=20,
            )
            if "data" in previous_data.json():
                previous_related_identifiers = previous_data.json()["data"]["attributes"]["relatedIdentifiers"]
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
                        "attributes": {"relatedIdentifiers": previous_related_identifiers},
                    }
                }

                request = requests.put(
                    url=url,
                    json=previous_version_request_metadata,
                    headers={"Content-type": "application/vnd.api+json"},
                    auth=(username, password),
                    timeout=20,
                )
                if request.status_code != HTTPStatus.OK:
                    raise requests.ConnectionError(
                        f"Expected status code {HTTPStatus.OK}, but got {request.status_code}"
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
                timeout=20,
            )
            if request.status_code != HTTPStatus.OK:
                raise requests.ConnectionError(f"Expected status code {HTTPStatus.OK}, but got {request.status_code}")

    def register_parent_doi(
        self, record: Any, request_metadata: dict, creds: tuple[str, str, str], rec_doi: str
    ) -> Any:
        """Register canonical DOI."""
        username, password, prefix = creds

        parent_request_metadata = copy.deepcopy(request_metadata)
        parent_request_metadata["data"]["attributes"]["prefix"] = str(prefix)
        parent_request_metadata["data"]["attributes"]["event"] = "publish"
        related_identifiers = parent_request_metadata["data"]["attributes"].get("relatedIdentifiers", [])
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
        parent_request_metadata["data"]["attributes"]["relatedIdentifiers"] = related_identifiers
        request = requests.post(
            url=self.url,
            json=parent_request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
            timeout=20,
        )
        if request.status_code != HTTPStatus.CREATED:
            raise requests.ConnectionError(f"Expected status code {HTTPStatus.CREATED}, but got {request.status_code}")

        content = request.content.decode("utf-8")
        json_content = json.loads(content)
        doi_value = json_content["data"]["id"]
        BaseProvider.create("doi", doi_value, "rec", record.parent.id, "R")
        self.add_doi_value(record, record, doi_value, parent=True)
        db.session.commit()
        return doi_value

    def update_parent_doi(
        self, record: Record, request_metadata: dict, username: str, password: str, rec_doi: str
    ) -> None:
        """Update canonical DOI."""
        parent_request_metadata = copy.deepcopy(request_metadata)
        doi_versions = self.get_doi_versions(record)
        if rec_doi not in doi_versions:
            doi_versions.append(rec_doi)
        related_identifiers = parent_request_metadata["data"]["attributes"].get("relatedIdentifiers", [])
        for doi_version in doi_versions:
            related_identifiers.append(
                {
                    "relationType": "HasVersion",
                    "relatedIdentifier": doi_version,
                    "relatedIdentifierType": "DOI",
                }
            )
        parent_request_metadata["data"]["attributes"]["relatedIdentifiers"] = related_identifiers

        url = self.url.rstrip("/") + "/" + self.get_doi_value(record, parent=True).replace("/", "%2F")
        request = requests.put(
            url=url,
            json=parent_request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
            timeout=20,
        )
        if request.status_code != HTTPStatus.OK:
            raise requests.ConnectionError(f"Expected status code {HTTPStatus.OK}, but got {request.status_code}")

    @override
    def update(self, pid: Any, **kwargs: Any) -> None:
        """Update information about the persistent identifier."""

    def update_doi(self, record: Any, **kwargs: Any) -> None:  # noqa C901
        """Update information about the persistent identifier."""
        doi_value = self.get_doi_value(record)
        if doi_value:
            creds = self.credentials(record)
            if creds is None:
                raise ValidationError(message="No credentials provided.")
            username, password, prefix = creds

            errors = self.metadata_check(record)
            record_service = get_record_service_for_record(record)
            if record_service is not None and hasattr(record_service, "links_item_tpl"):
                record["links"] = record_service.links_item_tpl.expand(system_identity, record)
                if errors:
                    raise ValidationError(message=errors)

                url = self.url.rstrip("/") + "/" + doi_value.replace("/", "%2F")

                request_metadata: dict[str, Any] = {"data": {"type": "dois", "attributes": {}}}
                payload = self.create_datacite_payload(record)
                request_metadata["data"]["attributes"] = payload

                parent_doi = self.get_pid_doi_value(record, parent=True)

                if parent_doi is None and "event" in kwargs:
                    parent_doi = self.register_parent_doi(
                        record, request_metadata, (username, password, prefix), doi_value
                    )
                elif parent_doi and record.versions.is_latest:
                    self.update_parent_doi(record, request_metadata, username, password, doi_value)
                related_identifiers = request_metadata["data"]["attributes"].get("relatedIdentifiers", [])

                if "event" in kwargs:
                    request_metadata["data"]["attributes"]["event"] = kwargs["event"]

                request_metadata["data"]["attributes"]["relatedIdentifiers"] = related_identifiers

                request = requests.put(
                    url=url,
                    json=request_metadata,
                    headers={"Content-type": "application/vnd.api+json"},
                    auth=(username, password),
                    timeout=20,
                )
                if request.status_code != HTTPStatus.OK:
                    raise requests.ConnectionError(
                        f"Expected status code {HTTPStatus.OK}, but got {request.status_code}"
                    )

                if "event" in kwargs:
                    pid_value = self.get_pid_doi_value(record)
                    if pid_value is not None and hasattr(pid_value, "status") and pid_value.status == "K":
                        pid_value.register()
                if parent_doi and record.is_published:
                    self.update_relations(parent_doi, record)

    def delete_draft(self, record: Record) -> None:
        """Remove doi from draft record and delete it from Datacite."""
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
            timeout=20,
        )
        if response.status_code != HTTPStatus.NO_CONTENT:
            raise requests.ConnectionError(
                f"Expected status code {HTTPStatus.NO_CONTENT}, but got {response.status_code}"
            )
        pid_value = self.get_pid_doi_value(record)
        if pid_value is not None:
            pid_value.delete()
            pid_value.unassign()
        self.remove_doi_value(record)

    def delete_published(self, record: Record) -> None:
        """Remove doi from published record and change it in Datacite to status registered."""
        creds = self.credentials(record)
        if creds is None:
            raise ValidationError("No credentials provided.")
        username, password, _ = creds
        doi_value = self.get_doi_value(record)
        request_metadata = {"data": {"type": "dois", "attributes": {"event": "hide"}}}

        if self.get_doi_versions(record) == [doi_value]:
            url = self.url.rstrip("/") + "/" + self.get_doi_value(record, parent=True).replace("/", "%2F")
            requests.put(
                url=url,
                json=request_metadata,
                headers={"Content-type": "application/vnd.api+json"},
                auth=(username, password),
                timeout=20,
            )
        url = self.url.rstrip("/") + "/" + doi_value.replace("/", "%2F")

        request = requests.put(
            url=url,
            json=request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
            timeout=20,
        )
        if request.status_code != HTTPStatus.OK:
            raise requests.ConnectionError(f"Expected status code {HTTPStatus.OK}, but got {request.status_code}")
        pid_value = self.get_pid_doi_value(record)
        if pid_value is not None:
            pid_value.delete()

    def create_datacite_payload(self, data: dict) -> dict:
        """Create payload for datacite server."""
        _ = data
        return {}

    def community_slug_for_credentials(self, value: str) -> Any:
        """Get community slug."""
        if not value:
            return None

        try:
            uuid.UUID(value, version=4)
            search = current_communities.service._search(  # noqa
                "search",
                system_identity,
                {},
                None,
                extra_filter=dsl.Q("term", id=value),
            )
            community = search.execute()
            c = next(iter(community.hits.hits))
            return c._source.slug  # noqa
        except:  # noqa: E722
            return value

    def get_versions(self, record: Any) -> Any:
        """Get record versions."""
        svc = get_record_service_for_record(record)
        if svc is None or not hasattr(svc, "search_versions"):
            return []
        pid = getattr(record, "pid", None)
        if pid is None or getattr(pid, "pid_value", None) is None:
            return []
        svc = cast("Any", svc)  # tell the checker "trust me, it has search_versions"
        versions = svc.search_versions(identity=system_identity, id_=pid.pid_value, params={"size": 1000})
        return versions.to_dict()["hits"]["hits"]

    def get_previous_version(self, record: Record) -> Any:
        """Get previous version of a record with DOI."""
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

    def get_doi_versions(self, record: Record) -> list:
        """Get list of all record versions with DOI."""
        versions_hits = self.get_versions(record)
        doi_versions = []
        for version in versions_hits:
            pids = version.get("pids", {})
            if "doi" in pids and "provider" in pids["doi"] and pids["doi"]["provider"] == "datacite":
                doi_versions.append(pids["doi"]["identifier"])
        return doi_versions

    def get_doi_value(self, record: Any, parent: bool = False) -> Any:
        """Get DOI value."""
        pids = record.parent.get("pids", {}) if parent else record.get("pids", {})
        return pids.get("doi", {}).get("identifier")

    def get_pid_doi_value(self, record: Any, parent: bool = False) -> PersistentIdentifier | None:
        """Get DOI PID object."""
        _id = record.parent.id if parent else record.id
        try:
            return PersistentIdentifier.get_by_object("doi", "rec", _id)
        except PersistentIdentifierError:
            return None

    def add_doi_value(self, record: Any, data: Any, doi_value: str, parent: bool = False) -> None:
        """Add DOI to record definition."""
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

    def remove_doi_value(self, record: Record) -> None:
        """Remove doi value from record definition."""
        pids = record.get("pids", {})
        if "doi" in pids:
            pids.pop("doi")
        record.commit()
