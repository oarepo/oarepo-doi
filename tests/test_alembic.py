# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for Alembic migrations."""

from __future__ import annotations

from unittest.mock import Mock

from oarepo_doi.alembic import settings_tables


def test_settings_tables_upgrade_creates_community_doi_settings_table(monkeypatch):
    """Settings table migration creates community DOI settings table."""
    op = Mock()
    op.f.side_effect = lambda name: name
    monkeypatch.setattr(settings_tables, "op", op)

    settings_tables.upgrade()

    op.create_table.assert_called_once()
    table_name, *columns_and_constraints = op.create_table.call_args.args
    assert table_name == "community_doi_settings"
    assert {column.name for column in columns_and_constraints if hasattr(column, "name")} >= {
        "created",
        "updated",
        "id",
        "prefix",
        "username",
        "password",
        "community_slug",
    }
