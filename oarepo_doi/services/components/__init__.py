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

from typing import TYPE_CHECKING, Any

from invenio_records_resources.services.records.components import ServiceComponent

from ..doi_client import DOIClient
from ..doi_provider import DOIProvider
from ..relations import update_doi_relations

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records.api import Record


class DoiComponent(ServiceComponent):
    """DOI component."""

    def update_draft(
        self, identity: Identity, data: Any | None = None, record: Any | None = None, **kwargs: Any
    ) -> None:
        """Update draft record."""
        _, _, _ = identity, data, kwargs
        if not DOIClient().credentials(
            record=record,
        ):
            return
        provider = DOIProvider()
        if provider.get_doi_value(record) and record is not None and hasattr(record, "is_published"):
            if not record.is_published:
                provider.create(record=record, new=False, publish=False)
                provider.create_canonical(record=record, new=False)
            else:
                provider.create(record=record, new=False, publish=False)
                provider.create_canonical(record=record, new=False)
            update_doi_relations(record)

    def update(self, identity: Identity, data: Any | None = None, record: Record | None = None, **kwargs: Any) -> None:
        """Update published record."""
        _, _, _ = identity, data, kwargs
        if not DOIClient().credentials(
            record=record,
        ):
            return
        provider = DOIProvider()
        if provider.get_doi_value(record):
            provider.create(record=record, new=False, publish=False)
            provider.create_canonical(record=record, new=False)

            update_doi_relations(record)

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
        if not DOIClient().credentials(
            record=record,
        ):
            return
        provider = DOIProvider()
        if provider.get_doi_value(record):
            new = not provider.get_doi_value(record)
            provider.create(record=record, new=new, publish=True)
            if record is not None and hasattr(record, "parent"):
                new = not provider.get_doi_value(record.parent)
                provider.create_canonical(record=record, new=new)

            update_doi_relations(record)

    def new_version(self, identity: Identity, draft: Record, record: Record | None = None, **kwargs: Any) -> None:
        """Update draft metadata."""
        _, _, _ = identity, record, kwargs
        provider = DOIProvider()
        doi_value = provider.get_doi_value(draft)
        if doi_value is not None:
            provider.remove_doi_value(draft)

    def delete_record(self, identity: Identity, record: Record, **kwargs: Any) -> None:
        """Delete published with DOI."""
        _, _ = identity, kwargs
        if not DOIClient().credentials(
            record=record,
        ):
            return
        provider = DOIProvider()
        provider.delete(record)
        provider.delete_canonical(
            record,
        )
        provider.create_canonical(record, new=False)
        update_doi_relations(record)

    def delete_draft(
        self, identity: Identity, draft: Record, record: Record | None = None, force: bool = False
    ) -> None:
        """Delete draft with DOI."""
        _, _, _ = identity, record, force
        if not DOIClient().credentials(draft):
            return
        provider = DOIProvider()
        provider.delete(draft)
        provider.delete_canonical(draft)
        provider.create_canonical(draft, new=False)
        update_doi_relations(draft)
