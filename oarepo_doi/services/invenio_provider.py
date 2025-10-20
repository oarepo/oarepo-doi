#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI oarepo provider."""

from invenio_rdm_records.services.pids.providers.base import PIDProvider
from typing import TYPE_CHECKING, Any, override
if TYPE_CHECKING:
    from invenio_records.api import Record
class MutedPIDProvider(PIDProvider):

    @classmethod
    @override
    def is_enabled(cls, app) -> Any:
        """Check if is enabled."""
        _ = app
        return True

    def metadata_check(
            self, record, schema: Any | None = None, provider: PIDProvider | None = None, **kwargs: Any
    ) -> list:
        """Check metadata against schema."""
        _, _, _, _ = record, schema, provider, kwargs

        return []

    def create(self, record, pid_value=None, status=None, **kwargs):
        """Get or create the PID with given value for the given record."""
        pass

    def reserve(self, pid, **kwargs):
        """Reserve a persistent identifier."""
        pass

    def register(self, pid, **kwargs):
        """Register a persistent identifier."""
        pass

    def update(self, pid, **kwargs):
        """Update information about the persistent identifier."""
        pass

    def restore(self, pid, **kwargs):
        """Update information about the persistent identifier."""
        pass

    def delete(self, pid, soft_delete=False, **kwargs):
        """Delete a persistent identifier."""
        pass

    def validate(self, record, identifier=None, provider=None, **kwargs):
        """Validate the attributes of the identifier."""
        pass

    def validate_restriction_level(self, record, identifier, **kwargs):
        """Validates that the record has correct restriction levels to crate the PID."""
        pass

    def create_and_reserve(self, record, **kwargs):
        """Create and reserve a PID for a record."""
        pass
