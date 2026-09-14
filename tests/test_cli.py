from types import SimpleNamespace
from unittest.mock import Mock, call

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
