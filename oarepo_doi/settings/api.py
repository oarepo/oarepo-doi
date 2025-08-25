#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI settings api."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override
from uuid import UUID

from invenio_db import db
from invenio_records.dumpers import SearchDumper
from invenio_records.dumpers.indexedat import IndexedAtDumperExt
from invenio_records.systemfields import ModelField
from invenio_records_resources.records.systemfields import IndexField
from invenio_users_resources.records.api import AggregatePID, BaseAggregate

from .models import CommunityDoiSettings, CommunityDoiSettingsAggregateModel

if TYPE_CHECKING:
    from invenio_records.api import Record


class CommunityDoiSettingsAggregate(BaseAggregate):
    """An aggregate of information about a community doi settings."""

    model_cls = CommunityDoiSettingsAggregateModel
    """The model class for the request."""

    dumper = SearchDumper(
        extensions=[IndexedAtDumperExt()],
        model_fields={
            "id": ("uuid", UUID),
        },
    )

    prefix = ModelField("prefix", dump_type=str)

    username = ModelField("username", dump_type=str)

    id = ModelField("id", dump_type=UUID)  # type: ignore[assignment]

    password = ModelField("password", dump=False)

    community_slug = ModelField("community_slug", dump_type=str)

    index = IndexField("doi-settings-doi-settings-v1.0.0", search_alias="doi-settings")

    """Needed to emulate pid access."""
    pid = AggregatePID("id")

    @classmethod
    @override
    def create(cls, data: dict, id_: str | None = None, **kwargs: Any) -> BaseAggregate:
        """Create a domain."""
        return CommunityDoiSettingsAggregate(
            data,
            model=CommunityDoiSettingsAggregateModel(model_obj=CommunityDoiSettings()),
        )

    @classmethod
    @override
    def get_record(cls, id_: str, with_deleted: bool = False) -> Record:
        """Get the user via the specified ID."""
        with db.session.no_autoflush:
            settings = CommunityDoiSettings.query.get(id_)
            if settings is not None:
                settings.password = ""

            return cls.from_model(settings)

    @override
    def delete(self, force: bool = True) -> Any:
        """Delete the domain."""
        db.session.delete(self.model.model_obj)
