# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for cli commands."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import oarepo_doi.cli as cli


def test_doi_update_command(app, monkeypatch):
    app.cli.add_command(cli.doi_cli)

    record = {
        "id": "1",
        "pids": {
            "doi": {
                "identifier": "10.1234/jej",
                "provider": "datacite",
            },
        },
    }

    monkeypatch.setattr(
        cli,
        "get_records_for_identifiers",
        lambda identifiers: [
            ("10.1234/example", record, None),
        ],
    )

    pid = SimpleNamespace(
        is_registered=lambda: True,
        status="R",
    )
    persistent_identifier = SimpleNamespace(
        get=Mock(return_value=pid),
    )
    monkeypatch.setattr(
        cli,
        "PersistentIdentifier",
        persistent_identifier,
    )

    register_or_update = Mock()
    service = SimpleNamespace(
        pids=SimpleNamespace(
            register_or_update=register_or_update,
        ),
    )
    monkeypatch.setattr(
        cli,
        "current_rdm_records_service",
        service,
    )

    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["doi", "update", "10.1234/jej"],
    )

    assert result.exit_code == 0
    assert "UPDATED 10.1234/jej (record 1)" in result.output
    assert "Updated: 1; skipped: 0; failed: 0" in result.output


def test_doi_with_fail(app, monkeypatch):
    app.cli.add_command(cli.doi_cli)

    records = [
        (
            "10.1234/first",
            {
                "id": "1",
                "pids": {
                    "doi": {
                        "identifier": "10.1234/first",
                        "provider": "datacite",
                    },
                },
            },
            None,
        ),
        (
            "10.1234/second",
            {
                "id": "2",
                "pids": {
                    "doi": {
                        "identifier": "10.1234/second",
                        "provider": "datacite",
                    },
                },
            },
            None,
        ),
        ("10.1234/failed", None, "record lookup failed"),
    ]
    get_all_records = Mock(return_value=records)
    monkeypatch.setattr(cli, "get_all_records_with_doi", get_all_records)

    pid = SimpleNamespace(
        is_registered=lambda: True,
        status="R",
    )
    monkeypatch.setattr(
        cli,
        "PersistentIdentifier",
        SimpleNamespace(get=Mock(return_value=pid)),
    )

    register_or_update = Mock()
    monkeypatch.setattr(
        cli,
        "current_rdm_records_service",
        SimpleNamespace(
            pids=SimpleNamespace(
                register_or_update=register_or_update,
            ),
        ),
    )

    runner = app.test_cli_runner()
    result = runner.invoke(args=["doi", "update", "--yes"])

    assert result.exit_code == 1
    assert "UPDATED 10.1234/first (record 1)" in result.output
    assert "UPDATED 10.1234/second (record 2)" in result.output
    assert "FAILED  10.1234/failed: record lookup failed" in result.output
    assert "Updated: 2; skipped: 0; failed: 1" in result.output
    assert "1 DOI update(s) failed" in result.output
