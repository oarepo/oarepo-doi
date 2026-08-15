#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for DOI settings proxies."""

from __future__ import annotations

from types import SimpleNamespace

from oarepo_doi.settings.proxies import current_doi_settings


def test_current_doi_settings_proxy(app):
    """Current DOI settings proxy resolves to extension from current app."""
    doi_settings = SimpleNamespace()
    app.extensions["doi-settings"] = doi_settings

    assert current_doi_settings._get_current_object() is doi_settings
