#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for DOI extension configuration initialization."""

from __future__ import annotations

from types import SimpleNamespace

from oarepo_doi.ext import OARepoDOI


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
    parent_provider_names = [
        provider.name for provider in app.config["RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS"]
    ]

    assert provider_names == ["oai", "datacite"]
    assert parent_provider_names == ["oai", "datacite"]

    assert set(app.config["RDM_PERSISTENT_IDENTIFIERS"]) == {'oai', 'doi'}
    assert set(app.config["RDM_PARENT_PERSISTENT_IDENTIFIERS"]) == {'oai', 'doi'}



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


