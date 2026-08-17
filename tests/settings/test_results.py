# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for DOI settings results."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from oarepo_doi.settings.results import CommunityDoiSettingsItem


def test_community_doi_settings():
    """Result item dumps DOI settings data and adds links."""
    identity = SimpleNamespace(id="identity")
    doi_settings = SimpleNamespace(id="settings-id")
    schema = SimpleNamespace(dump=Mock(return_value={"id": "settings-id"}))
    links_tpl = SimpleNamespace(expand=Mock(return_value={"self": "/doi_settings/settings-id"}))
    service = SimpleNamespace(schema=schema)

    item = CommunityDoiSettingsItem(service, identity, doi_settings, links_tpl=links_tpl)
    assert item._obj is doi_settings
    assert item.data == {
        "id": "settings-id",
        "links": {"self": "/doi_settings/settings-id"},
    }


def test_community_doi_settings_item():
    """Result item returns prefetched data without dumping the record."""
    schema = SimpleNamespace(dump=Mock())
    service = SimpleNamespace(schema=schema)
    data = {"id": "settings-id"}

    item = CommunityDoiSettingsItem(
        service,
        SimpleNamespace(),
        SimpleNamespace(id="settings-id"),
        data=data,
    )

    assert item.data is data
