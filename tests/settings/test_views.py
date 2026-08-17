# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for DOI settings views."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from oarepo_doi.settings.views import create_api_blueprint


def test_create_api_blueprint_uses_doi_settings_resource(app):
    """API blueprint is created from the DOI settings resource."""
    blueprint = Mock()
    doi_settings_resource = SimpleNamespace(as_blueprint=Mock(return_value=blueprint))
    app.extensions["doi-settings"] = SimpleNamespace(doi_settings_resource=doi_settings_resource)

    assert create_api_blueprint(app) is blueprint
