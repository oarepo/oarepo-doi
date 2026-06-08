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
from typing import TYPE_CHECKING

from invenio_base.utils import obj_or_import_string

from .config import (
    DOI_SETTINGS_FACETS,
    DOI_SETTINGS_SEARCH,
    DOI_SETTINGS_SORT_OPTIONS,
    RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS,
    RDM_PARENT_PERSISTENT_IDENTIFIERS,
    RDM_PERSISTENT_IDENTIFIER_PROVIDERS,
    RDM_PERSISTENT_IDENTIFIERS,
)

if TYPE_CHECKING:
    from typing import Any

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
        app.config.setdefault(
            "RDM_PERSISTENT_IDENTIFIER_PROVIDERS",
            RDM_PERSISTENT_IDENTIFIER_PROVIDERS,
        )
        app.config.setdefault(
            "RDM_PERSISTENT_IDENTIFIERS",
            RDM_PERSISTENT_IDENTIFIERS,
        )
        app.config.setdefault(
            "RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS",
            RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS,
        )
        app.config.setdefault(
            "RDM_PARENT_PERSISTENT_IDENTIFIERS",
            RDM_PARENT_PERSISTENT_IDENTIFIERS,
        )
        app.config.setdefault("DOI_SETTINGS_SEARCH", DOI_SETTINGS_SEARCH)
        app.config.setdefault("DOI_SETTINGS_FACETS", DOI_SETTINGS_FACETS)
        app.config.setdefault("DOI_SETTINGS_SORT_OPTIONS", DOI_SETTINGS_SORT_OPTIONS)

    @cached_property
    def doi_settings_service(self) -> Any:
        """Get the OAI run service."""
        factory: Any = obj_or_import_string(
            self.app.config.get(
                "DOI_CONFIG_SERVICE",
                "oarepo_doi.settings.service:CommunityDoiSettingsService",
            ),
        )
        return factory(self.doi_settings_service_config)

    @cached_property
    def doi_settings_service_config(self) -> Any:
        """Get the OAI run service config."""
        factory: Any = obj_or_import_string(
            self.app.config.get(
                "DOI_CONFIG_SERVICE_CONFIG",
                "oarepo_doi.settings.service:CommunityDoiSettingsServiceConfig",
            ),
        )
        return factory.build(self.app)

    @cached_property
    def doi_settings_resource_config(self) -> Any:
        """Get the OAI run resource config."""
        factory: Any = obj_or_import_string(
            self.app.config.get(
                "DOI_CONFIG_RESOURCE_CONFIG",
                "oarepo_doi.settings.resource:CommunityDoiSettingsResourceConfig",
            ),
        )
        return factory()

    @cached_property
    def doi_settings_resource(self) -> Any:
        """Get the OAI run resource."""
        factory: Any = obj_or_import_string(
            self.app.config.get(
                "DOI_CONFIG_RESOURCE",
                "oarepo_doi.settings.resource:CommunityDoiSettingsResource",
            ),
        )
        return factory(self.doi_settings_resource_config, self.doi_settings_service)


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
