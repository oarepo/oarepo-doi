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

from collections.abc import Callable
from functools import wraps
from inspect import signature
from typing import TYPE_CHECKING, Any, TypeVar, cast

from datacite.errors import DataCiteError
from invenio_rdm_records.services.pids.providers.base import PIDProvider as BasePIDProvider
from invenio_rdm_records.services.pids.providers.datacite import DataCitePIDProvider
from invenio_rdm_records.utils import ChainObject

if TYPE_CHECKING:
    from invenio_pidstore.models import PersistentIdentifier
    from invenio_records_resources.records.api import Record

F = TypeVar("F", bound=Callable[..., Any])


def with_record_context(fn: F) -> F:  # noqa: UP047
    """Bind record to DataCite client while executing provider method."""
    sig = signature(fn)

    @wraps(fn)
    def wrapper(self: DataCiteRecordAwareProvider, *args: Any, **kwargs: Any) -> Any:
        if self.client is None:
            raise RuntimeError("DataCite client is not configured")

        bound = sig.bind_partial(self, *args, **kwargs)
        record = bound.arguments.get("record")
        if record is None:
            extra_kwargs = bound.arguments.get("kwargs", {})
            if isinstance(extra_kwargs, dict):
                record = extra_kwargs.get("record")

        with self.client.for_record(record):
            return fn(self, *args, **kwargs)

    return cast("F", wrapper)


def _is_restricted(record: Any) -> bool:
    if isinstance(record, ChainObject):
        return bool(record._child["access"]["record"] == "restricted")  # noqa: SLF001
    return bool(record["access"]["record"] == "restricted")


def _is_datacite_already_taken(error: Any) -> bool:
    text = str(error)
    return bool("This DOI has already been taken" in text)


class DataCiteRecordAwareProvider(DataCitePIDProvider):
    """DOI record aware provider."""

    def generate_id(self, record: Record, **kwargs: Any) -> str:
        """Generate a unique DOI."""
        # Delegate to client
        _ = kwargs
        if self.client is None:
            raise RuntimeError("DataCite client is not configured")
        return str(self.client.generate_doi(record))

    @with_record_context
    def register(self, pid: PersistentIdentifier, record: Record, **kwargs: Any) -> Any:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Register DOI or update DOI if already taken."""
        if _is_restricted(record):
            return False

        local_success = BasePIDProvider.register(self, pid)
        if not local_success:
            return False

        try:
            doc = self.serializer.dump_obj(record)
            url = kwargs["url"]
            self.client.api.public_doi(metadata=doc, url=url, doi=pid.pid_value)  # pyright: ignore[reportOptionalMemberAccess]
            return True  # noqa: TRY300

        except DataCiteError as e:
            if _is_datacite_already_taken(e):
                return self.update(pid, record=record, url=kwargs.get("url"))
            return False

    @with_record_context
    def update(
        self,
        pid: PersistentIdentifier,
        record: Record | dict[str, Any] | None = None,
        url: str | None = None,
        **kwargs: Any,
    ) -> Any:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Update metadata associated with a DOI.

        This can be called before/after a DOI is registered.
        :param pid: the PID to register.
        :param record: the record metadata for the DOI.
        :returns: `True` if is updated successfully.
        """
        return super().update(pid, record, url=url, **kwargs)

    @with_record_context
    def restore(self, pid: PersistentIdentifier, **kwargs: Any) -> Any:
        """Restore previously deactivated DOI."""
        return super().restore(pid, **kwargs)

    @with_record_context
    def delete(self, pid: PersistentIdentifier, **kwargs: Any) -> Any:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Delete/unregister a registered DOI.

        If the PID has not been reserved then it's deleted only locally.
        Otherwise, also it's deleted also remotely.
        :returns: `True` if is deleted successfully.
        """
        return super().delete(pid, **kwargs)

    @with_record_context
    def validate(
        self,
        record: Any = None,
        identifier: Any = None,
        provider: Any = None,
        **kwargs: Any,
    ) -> Any:
        """Validate the attributes of the identifier."""
        return super().validate(record, identifier=identifier, provider=provider, **kwargs)
