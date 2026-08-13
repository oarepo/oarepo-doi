#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for DOI settings service."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from invenio_records_resources.services.errors import PermissionDeniedError

from oarepo_doi.settings import service as service_module
from oarepo_doi.settings.service import (
    CommunityDoiSettingsLink,
    CommunityDoiSettingsService,
    CommunityDoiSettingsServiceConfig,
)


def test_community_doi_settings():
    """Item links use DOI settings record id."""
    variables = {}

    CommunityDoiSettingsLink.vars(SimpleNamespace(id="settings-id"), variables)

    assert variables == {"id": "settings-id"}

    service = CommunityDoiSettingsService(CommunityDoiSettingsServiceConfig.build(None))
    with pytest.raises(PermissionDeniedError):
        service.search()


def test_rebuild_index_indexes_all_doi_settings(monkeypatch):
    """Rebuild index sends all DOI settings ids to the indexer."""
    service = CommunityDoiSettingsService(CommunityDoiSettingsServiceConfig.build(None))
    indexer = SimpleNamespace(bulk_index=Mock())
    query = Mock()
    query.yield_per.return_value = [SimpleNamespace(id="id-1"), SimpleNamespace(id="id-2")]
    monkeypatch.setattr(service_module.db.session, "query", Mock(return_value=query))
    monkeypatch.setattr(CommunityDoiSettingsService, "indexer", property(lambda self: indexer))

    assert service.rebuild_index(SimpleNamespace()) is True

    query.yield_per.assert_called_once_with(1000)
    indexer.bulk_index.assert_called_once_with(["id-1", "id-2"])
