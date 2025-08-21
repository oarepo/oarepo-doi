#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI extension."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

from deepmerge import conservative_merger
from invenio_base.utils import obj_or_import_string

from .config import (
    DOI_SETTINGS_FACETS,
    DOI_SETTINGS_SEARCH,
    DOI_SETTINGS_SORT_OPTIONS,
    NOTIFICATIONS_BUILDERS,
)

if TYPE_CHECKING:
    from flask import Flask


class OARepoDOI:
    """OARepo DOI extension."""

    def __init__(self, app: Flask | None = None) -> None:
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Flask application initialization."""
        self.app = app
        app.extensions["doi-settings"] = self
        self.init_config(app)

    def init_config(self, app: Flask) -> None:
        """Initialize configuration."""
        if "DATACITE_URL" not in app.config:
            app.config["DATACITE_URL"] = "https://api.datacite.org/dois"
        if "DATACITE_MODE" not in app.config:
            app.config["DATACITE_MODE"] = "ON_EVENT"
        if "DATACITE_SPECIFIED_ID" not in app.config:
            app.config["DATACITE_SPECIFIED_ID"] = False

        app_notification_builders = app.config.setdefault("NOTIFICATIONS_BUILDERS", {})
        app.config["NOTIFICATIONS_BUILDERS"] = conservative_merger.merge(
            app_notification_builders, NOTIFICATIONS_BUILDERS
        )
        app.config.setdefault("DOI_SETTINGS_SEARCH", DOI_SETTINGS_SEARCH)
        app.config.setdefault("DOI_SETTINGS_FACETS", DOI_SETTINGS_FACETS)
        app.config.setdefault("DOI_SETTINGS_SORT_OPTIONS", DOI_SETTINGS_SORT_OPTIONS)

    @cached_property
    def doi_settings_service(self) -> Any:
        """Get the OAI run service."""
        cf = obj_or_import_string(
            self.app.config.get(
                "DOI_CONFIG_SERVICE",
                "oarepo_doi.settings.service:CommunityDoiSettingsService",
            ),
        )
        if cf is not None:
            return self.doi_settings_service_config
        return cf

    @cached_property
    def doi_settings_service_config(self) -> Any:
        """Get the OAI run service config."""
        cf = obj_or_import_string(
            self.app.config.get(
                "DOI_CONFIG_SERVICE_CONFIG",
                "oarepo_doi.settings.service:CommunityDoiSettingsServiceConfig",
            ),
        )
        if cf is not None:
            return cf.build(self.app)
        return cf

    @cached_property
    def doi_settings_resource_config(self) -> Any:
        """Get the OAI run resource config."""
        cf = obj_or_import_string(
            self.app.config.get(
                "DOI_CONFIG_RESOURCE_CONFIG",
                "oarepo_doi.settings.resource:CommunityDoiSettingsResourceConfig",
            ),
        )
        if cf is not None:
            return cf()
        return cf

    @cached_property
    def doi_settings_resource(self) -> Any:
        """Get the OAI run resource."""
        cf = obj_or_import_string(
            self.app.config.get(
                "DOI_CONFIG_RESOURCE",
                "oarepo_doi.settings.resource:CommunityDoiSettingsResource",
            ),
        )
        if cf is not None:
            return cf(self.doi_settings_resource_config, self.doi_settings_service)

        return cf


def api_finalize_app(app: Flask) -> None:
    """Finalize app."""
    finalize_app(app)


def finalize_app(app: Flask) -> None:
    """Finalize app."""
    init(app)


def init(app: Flask) -> None:
    """Init app."""
    ext = app.extensions["doi-settings"]
    sregistry = app.extensions["invenio-records-resources"].registry
    sregistry.register(ext.doi_settings_service, service_id=ext.doi_settings_service_config.service_id)
    # Register indexers
    iregistry = app.extensions["invenio-indexer"].registry
    iregistry.register(
        ext.doi_settings_service.indexer,
        indexer_id=ext.doi_settings_service_config.service_id,
    )
