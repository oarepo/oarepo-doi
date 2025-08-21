#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI components."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from flask import current_app
from invenio_records_resources.services.records.components import ServiceComponent

if TYPE_CHECKING:
    from collections.abc import Iterable

    from flask_principal import Identity
    from invenio_records.api import Record

    from oarepo_doi.services.provider import OarepoDataCitePIDProvider


class DoiComponent(ServiceComponent):
    """DOI component."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Construct DOI Component."""
        super().__init__(*args, **kwargs)

        self.mode = current_app.config.get("DATACITE_MODE")

    @property
    def provider(self) -> OarepoDataCitePIDProvider:
        """Return specific DOI provider."""
        providers: Iterable[Any] = current_app.config.get("RDM_PERSISTENT_IDENTIFIER_PROVIDERS") or ()
        for p in providers:
            if getattr(p, "name", None) == "datacite":
                return cast("OarepoDataCitePIDProvider", p)
        raise LookupError("Datacite provider not found in RDM_PERSISTENT_IDENTIFIER_PROVIDERS")

    def create(self, identity: Identity, data: Any | None = None, record: Record | None = None, **kwargs: Any) -> None:
        """Create record."""
        (
            _,
            _,
            _,
        ) = identity, data, kwargs
        if self.mode == "AUTOMATIC_DRAFT":
            self.provider.create_and_reserve(record)

    def update_draft(
        self, identity: Identity, data: Any | None = None, record: Any | None = None, **kwargs: Any
    ) -> None:
        """Update draft record."""
        _, _, _ = identity, data, kwargs
        if record is not None and (
            not record.is_draft or (not record.is_published and self.mode in {"AUTOMATIC_DRAFT", "ON_EVENT_DRAFT"})
        ):
            self.provider.update_doi(record)

    def update(self, identity: Identity, data: Any | None = None, record: Record | None = None, **kwargs: Any) -> None:
        """Update published record."""
        _, _, _ = identity, data, kwargs
        self.provider.update_doi(record)

    def publish(
        self,
        identity: Identity,
        data: Any | None = None,
        record: Any | None = None,
        draft: Record | None = None,
        **kwargs: Any,
    ) -> None:
        """Publish record and DOI."""
        _, _, _, _ = identity, data, draft, kwargs

        if not self.provider.get_doi_value(record) and self.provider.get_doi_value(record, parent=True):
            # if it is a new version and a canonical DOI already exists, DOI will be added automatically
            self.provider.create_and_reserve(record, event="publish")
        if record is not None and hasattr(record, "pids") and record.pids is None:
            record.pids = {}
        if self.mode == "AUTOMATIC":
            self.provider.create_and_reserve(record, event="publish")
        if self.mode in {"AUTOMATIC_DRAFT", "ON_EVENT_DRAFT"}:
            self.provider.update_doi(record, event="publish")

    def new_version(self, identity: Identity, draft: Record, record: Record | None = None, **kwargs: Any) -> None:
        """Update draft metadata."""
        _, _ = identity, kwargs
        doi_value = self.provider.get_doi_value(record)
        if doi_value is not None:
            self.provider.remove_doi_value(draft)

    def delete_record(self, identity: Identity, record: Record, **kwargs: Any) -> None:
        """Delete published with DOI."""
        _, _ = identity, kwargs
        doi_value = self.provider.get_doi_value(record)
        pid_doi = self.provider.get_pid_doi_value(record)
        if pid_doi is not None and hasattr(pid_doi, "status") and pid_doi.status.value == "R" and doi_value is not None:
            self.provider.delete_published(record)

    def delete_draft(
        self, identity: Identity, draft: Record, record: Record | None = None, force: bool = False
    ) -> None:
        """Delete draft with DOI."""
        _, _, _ = identity, record, force
        doi_value = self.provider.get_doi_value(draft)
        pid_doi = self.provider.get_pid_doi_value(draft)
        if pid_doi is not None and hasattr(pid_doi, "status") and pid_doi.status.value == "K" and doi_value is not None:
            self.provider.delete_draft(draft)
