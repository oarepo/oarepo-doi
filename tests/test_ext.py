# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for DOI extension configuration initialization."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Self

from oarepo_doi.ext import OARepoDOI


class ServiceConfig:
    """Service config factory test double."""

    service_id = "doi-service"

    @classmethod
    def build(cls, app) -> Self:
        """Build service config."""
        _ = app
        return cls()


class Service:
    """Service factory test double."""

    def __init__(self, config):
        """Initialize service."""
        self.config = config
        self.indexer = "doi-indexer"


class ResourceConfig:
    """Resource config factory test double."""


class Resource:
    """Resource factory test double."""

    def __init__(self, config, service):
        """Initialize resource."""
        self.config = config
        self.service = service


def test_config(app):
    """Configured PID identifiers are preserved and default DOI is added."""
    app.config["RDM_PERSISTENT_IDENTIFIER_PROVIDERS"] = [SimpleNamespace(name="oai")]
    app.config["RDM_PERSISTENT_IDENTIFIERS"] = {
        "oai": {
            "providers": ["oai"],
            "required": False,
        },
    }
    app.config["RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS"] = [SimpleNamespace(name="oai")]
    app.config["RDM_PARENT_PERSISTENT_IDENTIFIERS"] = {
        "oai": {
            "providers": ["oai"],
            "required": False,
        },
    }

    OARepoDOI().init_config(app)

    provider_names = [provider.name for provider in app.config["RDM_PERSISTENT_IDENTIFIER_PROVIDERS"]]
    parent_provider_names = [provider.name for provider in app.config["RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS"]]

    assert provider_names == ["oai", "datacite"]
    assert parent_provider_names == ["oai", "datacite"]

    assert set(app.config["RDM_PERSISTENT_IDENTIFIERS"]) == {"oai", "doi"}
    assert set(app.config["RDM_PARENT_PERSISTENT_IDENTIFIERS"]) == {"oai", "doi"}


def test_init_config_keeps_configured_doi_identifier(app):
    """Configured DOI identifier wins over the default DOI identifier."""
    app.config["RDM_PERSISTENT_IDENTIFIER_PROVIDERS"] = [SimpleNamespace(name="datacite")]
    app.config["RDM_PERSISTENT_IDENTIFIERS"] = {
        "doi": {
            "providers": ["custom-datacite"],
            "required": False,
        },
    }

    OARepoDOI().init_config(app)

    provider_names = [provider.name for provider in app.config["RDM_PERSISTENT_IDENTIFIER_PROVIDERS"]]
    assert provider_names == ["datacite"]
    assert app.config["RDM_PERSISTENT_IDENTIFIERS"]["doi"]["providers"] == ["custom-datacite"]
    assert app.config["RDM_PERSISTENT_IDENTIFIERS"]["doi"]["required"] is False


def test_init_app_sets_default_config(app):
    """Extension initializes itself and default DOI config."""
    ext = OARepoDOI(app)

    assert app.extensions["doi-settings"] is ext
    assert app.config["RDM_PERSISTENT_IDENTIFIER_PROVIDERS"][0].name == "datacite"
    assert app.config["RDM_PERSISTENT_IDENTIFIERS"]["doi"]["providers"] == ["datacite"]
    assert app.config["RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS"][0].name == "datacite"
    assert app.config["RDM_PARENT_PERSISTENT_IDENTIFIERS"]["doi"]["providers"] == ["datacite"]
    assert "DOI_SETTINGS_SEARCH" in app.config
    assert "DOI_SETTINGS_FACETS" in app.config
    assert "DOI_SETTINGS_SORT_OPTIONS" in app.config


def test_extension_factories(app):
    """Extension builds configured service and resource objects."""
    app.config.update(
        DOI_CONFIG_SERVICE=Service,
        DOI_CONFIG_SERVICE_CONFIG=ServiceConfig,
        DOI_CONFIG_RESOURCE_CONFIG=ResourceConfig,
        DOI_CONFIG_RESOURCE=Resource,
    )
    ext = OARepoDOI(app)

    assert ext.doi_settings_service.config is ext.doi_settings_service_config
    assert ext.doi_settings_resource.config is ext.doi_settings_resource_config
    assert ext.doi_settings_resource.service is ext.doi_settings_service
