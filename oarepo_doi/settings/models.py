#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI setting database and aggregation model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, ClassVar

from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from invenio_oauthclient.models import _secret_key
from invenio_users_resources.records.models import AggregateMetadata
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import EncryptedType, Timestamp
from sqlalchemy_utils.types import UUIDType

if TYPE_CHECKING:
    from flask_sqlalchemy import Model


class CommunityDoiSettings(db.Model, Timestamp):
    """Model for Community DOI settings."""

    __tablename__ = "community_doi_settings"

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )

    @declared_attr
    def community_slug(self) -> Any:
        """Community slug foreign key."""
        return db.Column(
            db.String(255),
            db.ForeignKey(CommunityMetadata.slug, ondelete="CASCADE"),
            unique=True,
        )

    prefix = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(EncryptedType(type_in=db.Text, key=_secret_key), nullable=False)


class CommunityDoiSettingsAggregateModel(AggregateMetadata):
    """Model class that does not correspond to a database table."""

    _properties: ClassVar[list[str]] = [
        "id",
        "community_slug",
        "prefix",
        "username",
        "password",
        "created",
        "updated",
    ]
    """Properties of this object that can be accessed."""

    _set_properties: ClassVar[list[str]] = [
        "community_slug",
        "prefix",
        "username",
        "password",
    ]
    """Properties of this object that can be set."""

    @property
    def model_obj(self) -> Model:
        """The actual model object behind this user aggregate."""
        if self._model_obj is None and self._data is not None:  # type: ignore[has-type]
            id_ = self._data.get("id")
            with db.session.no_autoflush:
                self._model_obj = CommunityDoiSettings.query.get(id_)
        return self._model_obj

    @property
    def version_id(self) -> int:
        """Return the version ID of the record."""
        return 1
