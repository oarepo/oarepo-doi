#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI settings components."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from flask import abort
from invenio_communities.communities.records.models import CommunityMetadata
from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.components import ServiceComponent
from sqlalchemy.exc import NoResultFound

if TYPE_CHECKING:
    from sqlalchemy import Identity

    from .api import CommunityDoiSettingsAggregate


class DoiSettingsComponent(ServiceComponent):
    """Service component."""

    def create(
        self,
        identity: Identity,
        data: dict | None = None,
        record: CommunityDoiSettingsAggregate | None = None,
        **kwargs: Any,
    ) -> None:
        """Inject fields into the record."""
        __, __ = identity, kwargs
        if record is not None and data is not None:
            record.prefix = data["prefix"]
            record.username = data["username"]
            record.password = data["password"]
            record.community_slug = data["community_slug"]
            try:
                CommunityMetadata.query.filter_by(slug=data["community_slug"]).one()
            except NoResultFound:
                abort(400, description=_("Community not found"))

    def update(
        self,
        identity: Identity,
        data: dict | None = None,
        record: CommunityDoiSettingsAggregate | None = None,
        **kwargs: Any,
    ) -> None:
        """Update record fields."""
        __, __ = identity, kwargs
        if record is not None and data is not None:
            record.prefix = data["prefix"]
            record.username = data["username"]
            record.password = data["password"]
            record.community_slug = data["community_slug"]
            try:
                CommunityMetadata.query.filter_by(slug=data["community_slug"]).one()
            except NoResultFound:
                abort(400, description=_("Community not found"))
