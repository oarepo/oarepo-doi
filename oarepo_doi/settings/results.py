#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Results for the oai_runs service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from invenio_records_resources.services.records.results import RecordItem, RecordList

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records.api import RecordBase
    from invenio_records_resources.services import LinksTemplate


class CommunityDoiSettingsItem(RecordItem):
    """Single DOI settings."""

    @override
    def __init__(
        self,
        service: Any,
        identity: Identity,
        doi_settings: RecordBase,
        errors: Any | None = None,
        links_tpl: LinksTemplate | None = None,
        schema: Any | None = None,
        data: Any | None = None,
    ):
        """Construct."""
        self._data = data
        self._errors = errors
        self._identity = identity
        self._doi_settings = doi_settings
        self._service = service
        self._links_tpl = links_tpl
        self._schema = schema or service.schema

    @property
    def id(self) -> str:
        """Identity of the oai_run."""
        return str(self._doi_settings.id)

    @property
    def links(self) -> Any:
        """Get links for this result item."""
        if self._links_tpl is not None:
            return self._links_tpl.expand(self._identity, self._doi_settings)
        return None

    @property
    def _obj(self) -> RecordBase:
        """Return the object to dump."""
        return self._doi_settings

    @property
    def data(self) -> Any:
        """Property to get the doi."""
        if self._data is not None:
            return self._data

        data = cast(
            "dict[str, Any]",
            self._schema.dump(
                self._obj,
                context={
                    "identity": self._identity,
                    "record": self._doi_settings,
                },
            ),
        )

        if self._links_tpl:
            data["links"] = self.links

        self._data = data
        return self._data


class CommunityDoiSettingsList(RecordList):
    """List of DOI settings results."""
