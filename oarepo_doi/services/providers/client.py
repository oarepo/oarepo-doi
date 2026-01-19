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

from typing import Any

from datacite import DataCiteRESTClient
from invenio_db import db
from invenio_rdm_records.services.pids.providers.datacite import DataCiteClient

from oarepo_doi.settings.models import CommunityDoiSettings

from ..utils import community_slug_for_credentials


class DataCiteRecordAwareClient(DataCiteClient):
    """DataCite Client that stores record context."""

    def __init__(
        self, name: str, config_prefix: Any | None = None, config_overrides: Any | None = None, **kwargs: Any
    ) -> None:
        """Construct."""
        super().__init__(name, config_prefix, config_overrides, **kwargs)
        self._record = None

    def for_record(self, record: Any) -> DataCiteClient:
        """Set record context and return self."""
        self._record = record
        return self

    @property
    def record(self) -> Any:
        """Set record."""
        return self._record

    def get_doi_settings(self, record: Any) -> CommunityDoiSettings | Any:
        """Get doi configuration for the record."""
        assert record is not None  # noqa S101
        slug = community_slug_for_credentials(self.record.get("communities", {}).get("default", None))
        return db.session.query(CommunityDoiSettings).filter_by(community_slug=slug).first()

    @property
    def api(self) -> DataCiteRESTClient:
        """DataCite REST API client instance."""
        doi_settings = self.get_doi_settings(self._record)
        test_mode_default = True

        self._api = DataCiteRESTClient(
            doi_settings.username,
            doi_settings.password,
            doi_settings.prefix,
            self.cfg("test_mode", test_mode_default),
        )

        return self._api
