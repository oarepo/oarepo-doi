# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for DOI settings proxies."""

from __future__ import annotations

from types import SimpleNamespace

from oarepo_doi.settings.proxies import current_doi_settings


def test_current_doi_settings_proxy(app):
    """Current DOI settings proxy resolves to extension from current app."""
    doi_settings = SimpleNamespace()
    app.extensions["doi-settings"] = doi_settings

    assert current_doi_settings._get_current_object() is doi_settings
