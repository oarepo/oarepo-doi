#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI record aware provider."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_rdm_records.services.pids.providers.datacite import DataCitePIDProvider

if TYPE_CHECKING:
    from invenio_pidstore.models import PersistentIdentifier
    from invenio_records_resources.records.api import Record


class DataCiteRecordAwareProvider(DataCitePIDProvider):
    """DOI record aware provider."""

    def generate_id(self, record: Record, **kwargs: Any) -> str:
        """Generate a unique DOI."""
        # Delegate to client
        _ = kwargs
        if self.client is None:
            raise RuntimeError("DataCite client is not configured")
        return str(self.client.for_record(record).generate_doi(record))

    def register(self, pid: PersistentIdentifier, record: Record, **kwargs: Any) -> Any:
        """Register a DOI via the DataCite API."""
        if self.client is None:
            raise RuntimeError("DataCite client is not configured")
        self.client.for_record(record)
        return super().register(pid, record, **kwargs)

    def update(self, pid: PersistentIdentifier, record: Record, url: str | None = None, **kwargs: Any) -> Any:
        """Update metadata associated with a DOI.

        This can be called before/after a DOI is registered.
        :param pid: the PID to register.
        :param record: the record metadata for the DOI.
        :returns: `True` if is updated successfully.
        """
        if self.client is None:
            raise RuntimeError("DataCite client is not configured")
        self.client.for_record(record)
        return super().update(pid, record, url=url, **kwargs)

    def restore(self, pid: PersistentIdentifier, **kwargs: Any) -> Any:
        """Restore previously deactivated DOI."""
        record = kwargs.get("record")
        if self.client is None:
            raise RuntimeError("DataCite client is not configured")
        self.client.for_record(record)
        return super().restore(pid, **kwargs)

    def delete(self, pid: PersistentIdentifier, **kwargs: Any) -> Any:
        """Delete/unregister a registered DOI.

        If the PID has not been reserved then it's deleted only locally.
        Otherwise, also it's deleted also remotely.
        :returns: `True` if is deleted successfully.
        """
        record = kwargs.get("record")
        if self.client is None:
            raise RuntimeError("DataCite client is not configured")
        self.client.for_record(record)
        return super().delete(pid, **kwargs)
