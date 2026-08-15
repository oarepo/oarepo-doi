#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for DOI settings components."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import NoResultFound
from werkzeug.exceptions import BadRequest

from oarepo_doi.settings import components as components_module
from oarepo_doi.settings.components import DoiSettingsComponent
from oarepo_doi.settings.models import CommunityDoiSettings


def _doi_settings_data(community_slug="test-community"):
    """Return DOI settings input data."""
    return {
        "prefix": "10.12345",
        "username": "datacite-user",
        "password": "datacite-password",
        "community_slug": community_slug,
    }


def test_create(monkeypatch):
    """Create copies input data to record when community exists."""
    component = DoiSettingsComponent(SimpleNamespace())
    record = SimpleNamespace()
    community_query = Mock()
    settings_query = Mock()
    community_query.filter_by.return_value.one.return_value = SimpleNamespace()
    settings_query.filter_by.return_value.one_or_none.return_value = None

    def query(model):
        if model is CommunityDoiSettings:
            return settings_query
        return community_query

    monkeypatch.setattr(components_module.db.session, "query", Mock(side_effect=query))

    component.create(SimpleNamespace(), data=_doi_settings_data(), record=record)

    assert record.prefix == "10.12345"
    assert record.username == "datacite-user"
    assert record.password == "datacite-password"
    assert record.community_slug == "test-community"



def test_create_rejects_duplicate(monkeypatch):
    """Create rejects duplicate fallback DOI settings."""
    component = DoiSettingsComponent(SimpleNamespace())
    settings_query = Mock()
    settings_query.filter_by.return_value.one_or_none.return_value = SimpleNamespace()
    monkeypatch.setattr(components_module.db.session, "query", Mock(return_value=settings_query))

    with pytest.raises(BadRequest):
        component.create(SimpleNamespace(), data=_doi_settings_data("*"), record=SimpleNamespace())


def test_update_rejects_missing_community(monkeypatch):
    """Update rejects DOI settings for an unknown community."""
    component = DoiSettingsComponent(SimpleNamespace())
    community_query = Mock()
    community_query.filter_by.return_value.one.side_effect = NoResultFound
    monkeypatch.setattr(components_module.db.session, "query", Mock(return_value=community_query))

    with pytest.raises(BadRequest):
        component.update(SimpleNamespace(), data=_doi_settings_data(), record=SimpleNamespace())

