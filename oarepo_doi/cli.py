# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""CLI commands for doi management."""

from __future__ import annotations

import click
from flask.cli import with_appcontext
from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_rdm_records.proxies import current_rdm_records_service


@click.group("doi")
def doi_cli() -> None:
    """Datarepo DOI maintenance commands."""


@doi_cli.command("update")
@click.argument(
    "identifiers",
    nargs=-1,
)
@click.option(
    "--yes",
    is_flag=True,
    help="Skip confirmation when updating all DOIs.",
)
@with_appcontext
def update(identifiers: tuple, yes: bool) -> None:  # noqa: C901, PLR0912, PLR0915
    """Update DataCite metadata for selected list or all DOIs."""
    if identifiers:
        records = get_records_for_identifiers(identifiers)
    else:
        if not yes:
            click.confirm("Update all managed DataCite DOIs?", abort=True)
        records = get_all_records_with_doi()

    updated = 0
    skipped = 0
    failed = 0
    seen: set[str] = set()

    for requested_identifier, record, lookup_error in records:
        if lookup_error is not None:
            failed += 1
            click.secho(f"FAILED  {requested_identifier}: {lookup_error}", fg="red")
            continue

        doi = get_doi_from_record(record)
        if doi is None:
            skipped += 1
            click.secho(
                f"SKIPPED {requested_identifier}: record has no DOI",
                fg="yellow",
            )
            continue

        identifier = doi.get("identifier")
        provider = doi.get("provider")
        if not identifier:
            skipped += 1
            click.secho(
                f"SKIPPED {requested_identifier}: DOI has no identifier",
                fg="yellow",
            )
            continue

        if identifier in seen:
            skipped += 1
            click.secho(f"SKIPPED {identifier}: duplicate", fg="yellow")
            continue
        seen.add(identifier)

        if provider != "datacite":
            skipped += 1
            click.secho(
                f"SKIPPED {identifier}: provider is {provider!r}, not DataCite",
                fg="yellow",
            )
            continue

        try:
            pid = PersistentIdentifier.get(
                pid_type="doi",
                pid_value=identifier,
            )
        except PIDDoesNotExistError:
            failed += 1
            click.secho(
                f"FAILED  {identifier}: DOI does not exist in PIDStore",
                fg="red",
            )
            continue

        if not pid.is_registered():
            skipped += 1
            click.secho(
                f"SKIPPED {identifier}: PID is not registered ({pid.status})",
                fg="yellow",
            )
            continue

        record_id = record.get("id")
        if not record_id:
            failed += 1
            click.secho(f"FAILED  {identifier}: record has no id", fg="red")
            continue

        try:
            current_rdm_records_service.pids.register_or_update(
                system_identity,
                record_id,
                "doi",
            )
            current_rdm_records_service.pids.register_or_update(  # for canonical doi
                system_identity,
                record_id,
                "doi",
                parent=True,
            )
        except Exception as exc:  # noqa: BLE001
            failed += 1
            click.secho(
                f"FAILED  {identifier} (record {record_id}): {exc}",
                fg="red",
            )
            continue

        updated += 1
        click.secho(f"UPDATED {identifier} (record {record_id})", fg="green")

    click.echo()
    click.echo(f"Updated: {updated}; skipped: {skipped}; failed: {failed}")

    if failed:
        raise click.ClickException(f"{failed} DOI update(s) failed")


def get_records_for_identifiers(identifiers: tuple) -> list:
    """Resolve explicitly requested DOI identifiers to published records."""
    records = []

    for identifier in identifiers:
        try:
            result = current_rdm_records_service.pids.resolve(
                system_identity,
                identifier,
                "doi",
            )
        except Exception as exc:  # noqa: BLE001
            records.append((identifier, None, str(exc)))
            continue

        records.append((identifier, result.to_dict(), None))

    return records


def get_all_records_with_doi() -> list:
    """Scan all published records containing a DOI."""
    results = current_rdm_records_service.scan(
        system_identity,
        params={"q": "_exists_:pids.doi.identifier"},
    )

    records = []
    for record in results:
        doi = get_doi_from_record(record)
        identifier = None

        if doi is not None:
            identifier = doi.get("identifier")

        if identifier is None:
            identifier = record.get("id", "<unknown>")

        record_entry = (identifier, record, None)
        records.append(record_entry)

    return records


def get_doi_from_record(record: dict | None) -> dict | None:
    """Return DOI attributes from a serialized record, if present."""
    if record is None:
        return None
    return record.get("pids", {}).get("doi")
