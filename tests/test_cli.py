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


def test_get_records_for_identifiers(monkeypatch):
    resolved_record = {"id": "1"}
    resolve = Mock(
        side_effect=[
            SimpleNamespace(to_dict=Mock(return_value=resolved_record)),
            RuntimeError("resolve failed"),
        ],
    )
    monkeypatch.setattr(
        cli,
        "current_rdm_records_service",
        SimpleNamespace(pids=SimpleNamespace(resolve=resolve)),
    )

    records = cli.get_records_for_identifiers(("10.1234/first", "10.1234/failed"))

    assert records == [
        ("10.1234/first", resolved_record, None),
        ("10.1234/failed", None, "resolve failed"),
    ]
    assert resolve.call_count == 2


def test_get_all_records_with_doi(monkeypatch):
    records = [
        {"id": "1", "pids": {"doi": {"identifier": "10.1234/first"}}},
        {"id": "2", "pids": {"doi": {}}},
        {"pids": {}},
    ]
    scan = Mock(return_value=records)
    monkeypatch.setattr(
        cli,
        "current_rdm_records_service",
        SimpleNamespace(scan=scan),
    )

    result = cli.get_all_records_with_doi()

    assert list(result) == [
        ("10.1234/first", records[0], None),
        ("2", records[1], None),
        ("<unknown>", records[2], None),
    ]
    scan.assert_called_once_with(
        cli.system_identity,
        params={"q": "_exists_:pids.doi.identifier"},
    )


def test_doi_update_handles_pid_and_update_errors(app, monkeypatch):
    app.cli.add_command(cli.doi_cli)

    records = [
        (
            "missing-identifier",
            {"id": "1", "pids": {"doi": {"provider": "datacite"}}},
            None,
        ),
        (
            "10.1234/missing-pid",
            {
                "id": "2",
                "pids": {"doi": {"identifier": "10.1234/missing-pid", "provider": "datacite"}},
            },
            None,
        ),
        (
            "10.1234/unregistered",
            {
                "id": "3",
                "pids": {"doi": {"identifier": "10.1234/unregistered", "provider": "datacite"}},
            },
            None,
        ),
        (
            "10.1234/update-failed",
            {
                "id": "4",
                "pids": {"doi": {"identifier": "10.1234/update-failed", "provider": "datacite"}},
            },
            None,
        ),
    ]
    monkeypatch.setattr(cli, "get_records_for_identifiers", Mock(return_value=records))

    unregistered_pid = SimpleNamespace(is_registered=lambda: False, status="N")
    registered_pid = SimpleNamespace(is_registered=lambda: True, status="R")

    def get_pid(*, pid_type, pid_value):
        assert pid_type == "doi"
        if pid_value == "10.1234/missing-pid":
            raise cli.PIDDoesNotExistError(pid_type, pid_value)
        if pid_value == "10.1234/unregistered":
            return unregistered_pid
        return registered_pid

    monkeypatch.setattr(cli, "PersistentIdentifier", SimpleNamespace(get=get_pid))

    register_or_update = Mock(side_effect=RuntimeError("DataCite unavailable"))
    monkeypatch.setattr(
        cli,
        "current_rdm_records_service",
        SimpleNamespace(pids=SimpleNamespace(register_or_update=register_or_update)),
    )

    result = app.test_cli_runner().invoke(
        args=["doi", "update", "first", "second", "third", "fourth"],
    )

    assert result.exit_code == 1
    assert "SKIPPED missing-identifier: DOI has no identifier" in result.output
    assert "FAILED  10.1234/missing-pid: DOI does not exist in PIDStore" in result.output
    assert "SKIPPED 10.1234/unregistered: PID is not registered (N)" in result.output
    assert "FAILED  10.1234/update-failed (record 4): DataCite unavailable" in result.output
    assert "Updated: 0; skipped: 2; failed: 2" in result.output
    assert register_or_update.call_count == 1
