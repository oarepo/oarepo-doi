#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI record aware client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from datacite import DataCiteRESTClient
from invenio_db import db
from invenio_rdm_records.services.pids.providers.datacite import DataCiteClient

from oarepo_doi.settings.models import CommunityDoiSettings

from ..utils import community_slug_for_credentials

if TYPE_CHECKING:
    from invenio_records_resources.records.api import Record


class DataCiteRecordAwareClient(DataCiteClient):
    """DataCite Client that stores record context."""

    def __init__(
        self,
        name: str,
        config_prefix: Any | None = None,
        config_overrides: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Construct."""
        super().__init__(name, config_prefix, config_overrides, **kwargs)
        self._record = None

    def for_record(self, record: Record) -> DataCiteClient:
        """Set record context and return self."""
        self._record = record
        return self

    @property
    def record(self) -> Any:
        """Set record."""
        return self._record

    def generate_doi(self, record: Record) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Generate a DOI."""
        doi_settings = self.get_doi_settings(record)
        if not doi_settings:
            return str(super().generate_doi(record))
        prefix = doi_settings.prefix
        doi_format = self.cfg("format", "{prefix}/{id}")
        if doi_format is None:
            doi_format = "{prefix}/{id}"
        if callable(doi_format):
            return str(doi_format(prefix, record))
        return str(doi_format.format(prefix=prefix, id=record.pid.pid_value))  # pyright: ignore[reportAttributeAccessIssue]

    def get_doi_settings(self, record: Record) -> CommunityDoiSettings | Any:
        """Get doi configuration for the record."""
        parent = getattr(record, "parent", None)
        if parent is not None:
            community = parent.get("communities", {}).get("default", None)
        else:
            community = record.get("communities", {}).get("default", None)
        slug = community_slug_for_credentials(community)

        return (
            db.session.query(CommunityDoiSettings).filter_by(community_slug=slug).first() if slug else None
        ) or db.session.query(CommunityDoiSettings).filter_by(community_slug="*").first()

    @property
    def api(self) -> DataCiteRESTClient:
        """DataCite REST API client instance."""
        doi_settings = self.get_doi_settings(self._record)  # pyright: ignore[reportArgumentType]
        if doi_settings is None:
            return super().api
        test_mode_default = True
        test_mode_cfg = self.cfg("test_mode", test_mode_default)
        test_mode = test_mode_cfg if isinstance(test_mode_cfg, bool) else test_mode_default

        self._api = DataCiteRESTClient(
            doi_settings.username,
            doi_settings.password,
            doi_settings.prefix,
            test_mode,
        )

        return self._api
