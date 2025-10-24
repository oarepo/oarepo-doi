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

from typing import TYPE_CHECKING, Any, cast, override

import requests  # type: ignore[import-untyped]
from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_rdm_records.services.pids.providers import DataCiteClient
from invenio_rdm_records.services.pids.providers.base import PIDProvider


if TYPE_CHECKING:
    from invenio_records.api import Record

EXPECTED_STATUS = {
        "GET": [200],
        "POST": [200, 201],
        "PUT": [200, 204],
        "DELETE": [200, 204],
    }

class MutedPIDProvider(PIDProvider):
    """Oarepo DOI provider."""
    def __init__(
            self,
            id_: str,
            client: DataCiteClient | None = None,
            serializer: Any | None = None,
            pid_type: str = "doi",
            default_status: PIDStatus = PIDStatus.NEW,
            **kwargs: Any,
    ):
        """Construct."""
        super().__init__(
            id_,
            client=(client or DataCiteClient("datacite", config_prefix="DATACITE")),
            pid_type=pid_type,
            default_status=default_status,
            **kwargs
        )
        self.serializer = serializer
        self.default_headers = {"Content-type": "application/vnd.api+json"}


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


    @override
    def generate_id(self, record: Any, **kwargs: Any) -> None:
        """Mute invenio method."""
        # done at DataCite level

    @classmethod
    @override
    def is_enabled(cls, app) -> Any:
        """Check if is enabled."""
        _ = app
        return True

    def can_modify(self, pid: PersistentIdentifier, **kwargs: Any) -> Any:
        """Check if can be modified."""
        _ = kwargs
        return not pid.is_registered()

    """Unused invenio function that needs to be silenced."""

    def register(self, pid: Any, **kwargs: Any) -> Any:
        """Mute invenio method."""

    def create(self, record: Any, pid_value: str | None = None, status: str | None = None, **kwargs: Any) -> Any:
        """Mute invenio method."""
        pass

    def restore(self, pid: Any, **kwargs: Any) -> Any:
        """Mute invenio method."""

    def delete(self, pid: Any, soft_delete: bool=False, **kwargs: Any) -> Any:
        """Mute invenio method."""
        pass

    def update(self, pid, **kwargs):
        """Mute invenio method."""

    """abstract methods"""
    def create_datacite_payload(self, data: dict) -> dict:
        """Create payload for datacite server."""
        _ = data
        return {}

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

    """provider functionality"""

    @override
    def validate_restriction_level(self, record: Record, identifier: str | None = None, **kwargs: Any) -> Any:
        """Check if record not restricted."""
        return True


    def datacite_request(self, record: Record, **kwargs: Any) -> Any:
        """Create Datacite request."""
        pass

    def create_and_reserve(self, record, **kwargs):
        pass



    def register_parent_doi(
        self, record, request_metadata, username, password, prefix, rec_doi
    ):
        pass

    def update_parent_doi(self, record, request_metadata, username, password, rec_doi):
        pass

    def update_doi(self, record, url=None, **kwargs):
        pass

    def delete_draft(self, record, **kwargs):
        pass

    def delete_published(self, record, **kwargs):
        pass


