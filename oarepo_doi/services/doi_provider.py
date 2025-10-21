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

from typing import TYPE_CHECKING, Any

from flask import current_app
from invenio_access.permissions import system_identity
from invenio_base.utils import obj_or_import_string
from invenio_db import db
from invenio_pidstore.errors import PIDAlreadyExists, PIDDoesNotExistError, PIDInvalidAction
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.providers.base import BaseProvider
from marshmallow import ValidationError
from oarepo_runtime.datastreams.utils import get_record_service_for_record

from oarepo_doi.services.doi_client import DOIClient

from .relations import get_doi_versions, get_latest

if TYPE_CHECKING:
    from invenio_records.api import Record


class DOIProvider:
    """DOI provider."""

    prefix = ""

    @property
    def mapping(self) -> Any:
        """Return DOI mode."""
        return obj_or_import_string(current_app.config.get("DATACITE_MAPPING"))()

    def generate_doi(self, record: Record) -> str:
        """Generate DOI."""
        return f"{self.prefix}/{record['id']}"

    def get_doi_value(self, record: Record) -> Any:
        """Get DOI."""
        pids = record.get("pids", {})
        return pids.get("doi", {}).get("identifier")

    def remove_doi_value(self, record: Record) -> None:
        """Remove DOI."""
        pids = record.get("pids", {})
        if "doi" in pids:
            pids.pop("doi")
        record.commit()

    def create_pid(self, record: Record, doi_value: str) -> None:
        """Create PID."""
        pid_status = "R" if not hasattr(record, "parent") else "N" if record.is_draft else "R"

        try:
            BaseProvider.create("doi", doi_value, "rec", record.id, pid_status)
            db.session.commit()
        except PIDAlreadyExists:
            pass

    def add_doi_value(self, record: Record, doi: str) -> None:
        """Add DOI."""
        pids = record.get("pids", {})
        pids["doi"] = {"provider": "datacite", "identifier": doi}

        record.pids = pids
        record.commit()

    def get_pid_doi_value(self, record: Record) -> Any:
        """Get PID."""
        try:
            return PersistentIdentifier.get_by_object("doi", "rec", record.id)
        except PIDDoesNotExistError:
            return None

    def create(self, record: Record, new: bool = True, publish: bool = False) -> Any:
        """Create DOI."""
        doi_value = self.get_doi_value(record)
        if (doi_value and new) or (not doi_value and not new):
            pass

        errors = self.mapping.metadata_check(record)
        if errors:
            raise ValidationError(message=errors)

        self.subcreate(record, publish, new)

    def subcreate(
        self, record: Record, publish: bool, new: bool, canonical: bool = False, canonical_rec: Any = None
    ) -> Any:
        """Prepare request."""
        client = DOIClient()
        credentials = client.credentials(record)
        if credentials is None:
            return None
        _, _, prefix = credentials
        self.prefix = prefix

        record_service = get_record_service_for_record(record)
        if record_service is not None and hasattr(record_service, "links_item_tpl"):
            record["links"] = record_service.links_item_tpl.expand(system_identity, record)

            request_metadata: dict[str, Any] = {"data": {"type": "dois", "attributes": {}}}
            data = record
            if canonical_rec:
                data = canonical_rec
            payload = self.mapping.create_datacite_payload(data)
            request_metadata["data"]["attributes"] = payload

            if canonical:
                record = record.parent
            doi = self.generate_doi(record)
            request_metadata["data"]["attributes"]["doi"] = doi

            if publish:
                request_metadata["data"]["attributes"]["event"] = "publish"
            client.datacite_request(request_metadata, record, "PUT")

            if new:
                self.create_pid(record, doi)
                self.add_doi_value(record, doi)
            elif publish and not new:
                try:
                    pid_value = self.get_pid_doi_value(record)
                    pid_value.register()
                except PIDInvalidAction:
                    pass

            return True

        return None

    def delete(self, record: Record, canonical: bool = False) -> None:
        """Delete DOI."""
        pid_value = self.get_pid_doi_value(record)
        if not pid_value:
            return

        client = DOIClient()

        if canonical or (hasattr(record, "is_published") and record.is_published):
            request_metadata = {"data": {"type": "dois", "attributes": {"event": "hide"}}}
            client.datacite_request(request_metadata, record, "PUT")
            pid_value.delete()
            self.remove_doi_value(record)
        else:
            client.datacite_request({}, record, method="DELETE")
            pid_value.unassign()
            pid_value.delete()
            self.remove_doi_value(record)

    def delete_canonical(self, record: Record) -> None:
        """Delete canonical DOI."""
        doi_value = self.get_doi_value(record.parent)
        if not doi_value:
            return
        doi_versions = get_doi_versions(record)
        if len(doi_versions) == 0:
            self.delete(record.parent, canonical=True)

    def create_canonical(self, record: Record, new: bool) -> Any:
        """Manage canonical DOI."""
        latest = get_latest(record)
        if not latest:
            return False
        return self.subcreate(record, publish=True, new=new, canonical=True, canonical_rec=latest)
