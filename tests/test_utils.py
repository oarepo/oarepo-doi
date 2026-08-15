#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for service utilities."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from oarepo_doi.services import utils
from oarepo_doi.services.utils import community_slug_for_credentials


def test_community_slug_for_credentials(monkeypatch):
    """Non-UUID community value is already a slug."""
    assert community_slug_for_credentials("test-community") == "test-community"
    assert community_slug_for_credentials(None) is None
    community_id = "00000000-0000-4000-8000-000000000000"
    search = SimpleNamespace(
        execute=Mock(
            return_value=SimpleNamespace(
                hits=SimpleNamespace(
                    hits=[SimpleNamespace(_source=SimpleNamespace(slug="test-community"))],
                ),
            ),
        ),
    )
    community_service = SimpleNamespace(_search=Mock(return_value=search))
    monkeypatch.setattr(
        utils,
        "current_communities",
        SimpleNamespace(service=community_service),
    )

    assert community_slug_for_credentials(community_id) == "test-community"
