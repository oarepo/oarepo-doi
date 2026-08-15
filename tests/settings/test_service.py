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


def test_read_returns_doi_settings_item(monkeypatch):
    """Read returns DOI settings item for existing record."""
    service = CommunityDoiSettingsService(CommunityDoiSettingsServiceConfig.build(None))
    identity = SimpleNamespace(id="identity")
    doi_config = SimpleNamespace(id="settings-id")
    result = SimpleNamespace(id="settings-id")
    get_record = Mock(return_value=doi_config)
    service.require_permission = Mock()
    service.result_item = Mock(return_value=result)
    monkeypatch.setattr(service_module.CommunityDoiSettingsAggregate, "get_record", get_record)

    assert service.read(identity, "settings-id") is result
