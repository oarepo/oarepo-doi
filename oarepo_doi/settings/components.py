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
from invenio_db import db
from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.components import ServiceComponent
from sqlalchemy.exc import NoResultFound

from oarepo_doi.settings.models import CommunityDoiSettings

if TYPE_CHECKING:
    from flask_principal import Identity

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
            if data["community_slug"] != "*":  # fallback value
                try:
                    db.session.query(CommunityMetadata).filter_by(slug=data["community_slug"]).one()
                except NoResultFound:
                    abort(400, description=_("Community not found"))

            existing_settings = (
                db.session.query(CommunityDoiSettings).filter_by(community_slug=data["community_slug"]).one_or_none()
            )

            if existing_settings:
                abort(
                    400,
                    description=_(
                        "Settings for this community already exist. "
                        "Please edit the existing settings instead of creating a new one."
                    ),
                )

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
                db.session.query(CommunityMetadata).filter_by(slug=data["community_slug"]).one()
            except NoResultFound:
                abort(400, description=_("Community not found"))
