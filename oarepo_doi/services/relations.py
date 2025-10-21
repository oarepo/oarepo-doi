#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI datacite relation module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError
from oarepo_runtime.datastreams.utils import get_record_service_for_record

from .doi_client import DOIClient

if TYPE_CHECKING:
    from invenio_records.api import Record

EXPECTED_STATUS = 200


def get_versions(record: Record) -> Any:
    """Get all record versions."""
    topic_service = get_record_service_for_record(record)
    try:
        versions = topic_service.search_versions(
            identity=system_identity, id_=record.pid.pid_value, params={"size": 1000}
        )
        versions_hits = versions.to_dict()["hits"]["hits"]
    except PIDDoesNotExistError:
        versions_hits = []
    return versions_hits


def get_doi_indices(record: Record) -> list:
    """Get dois from record versions with order indices."""
    versions = get_doi_versions(record)
    doi_indices = []
    for version in versions:
        for index, rec in version.items():
            pids = rec.get("pids", {})
            doi = pids["doi"]["identifier"]
            doi_indices.append({doi: index})
    return doi_indices


def get_doi_versions(record: Record) -> list:
    """Return record with existing datacite DOIs."""
    versions_hits = get_versions(record)
    existing_index = next((i for i, v in enumerate(versions_hits) if v.get("id") == record["id"]), None)

    if getattr(getattr(record, "deletion_status", None), "is_deleted", False):
        if existing_index is not None:
            del versions_hits[existing_index]
    elif existing_index is None:
        versions_hits.append(record.dumps())
    else:
        versions_hits[existing_index] = record.dumps()

    doi_versions = []
    seen = set()
    for version in versions_hits:
        if version.get("is_published"):
            pids = version.get("pids", {})
            versions = version.get("versions", {})
            if "doi" in pids and "provider" in pids["doi"] and pids["doi"]["provider"] == "datacite":
                doi = pids["doi"]["identifier"]
                if doi not in seen:
                    doi_versions.append({versions["index"]: version})
                    seen.add(doi)

    return doi_versions


def get_parent_doi(record: Record) -> Any:
    """Get parent DOI."""
    parent = record.parent
    pids = parent.get("pids", {})
    if "doi" in pids and "provider" in pids["doi"] and pids["doi"]["provider"] == "datacite":
        return pids["doi"]["identifier"]
    return None


def get_latest(record: Record) -> Any:
    """Get latest version with DOI."""
    versions = get_doi_versions(record)
    if not versions:
        return None

    latest = max(versions, key=lambda v: next(iter(v.keys())))

    return next(iter(latest.values()))


def update_relations(record: Record, parent_doi: str) -> None:
    """Update relations between versions."""
    doi_client = DOIClient()

    relations = get_doi_indices(record)
    pairs = [(next(iter(d.keys())), next(iter(d.values()))) for d in relations]
    url = current_app.config["DATACITE_URL"]
    pairs.sort(key=lambda x: x[1])
    exclude = {"IsVersionOf", "IsPreviousVersionOf", "IsNewVersionOf"}

    sorted_dois = [id_ for id_, _ in pairs]

    for idx, doi in enumerate(sorted_dois):
        doi_url = url.rstrip("/") + "/" + doi.replace("/", "%2F")
        response = requests.get(url=doi_url, timeout=20)

        data = response.json()

        related_identifiers = data["data"]["attributes"].get("relatedIdentifiers", {})

        cleaned = [ri for ri in related_identifiers if ri.get("relationType") not in exclude]

        additions = []

        additions.append(
            {
                "relationType": "IsVersionOf",
                "relatedIdentifier": parent_doi,
                "relatedIdentifierType": "DOI",
            }
        )

        if idx > 0:
            prev_doi = sorted_dois[idx - 1]
            additions.append(
                {
                    "relationType": "IsNewVersionOf",
                    "relatedIdentifier": prev_doi,
                    "relatedIdentifierType": "DOI",
                }
            )

        if idx < len(sorted_dois) - 1:
            next_doi = sorted_dois[idx + 1]
            additions.append(
                {
                    "relationType": "IsPreviousVersionOf",
                    "relatedIdentifier": next_doi,
                    "relatedIdentifierType": "DOI",
                }
            )

        new_related_identifiers = cleaned + additions
        data["data"]["attributes"]["relatedIdentifiers"] = new_related_identifiers
        doi_client.datacite_request(data, record, method="PUT", url=doi_url)


def update_parent_relations(record: Record) -> None:
    """Update parent relations."""
    doi_client = DOIClient()

    parent_doi = get_parent_doi(record)
    if parent_doi is None:
        return
    relations = get_doi_indices(record)

    url = current_app.config["DATACITE_URL"]
    parent_doi_url = url.rstrip("/") + "/" + parent_doi.replace("/", "%2F")

    response = requests.get(
        url=parent_doi_url,
        timeout=20,
    )
    if response.status_code != EXPECTED_STATUS:
        raise requests.ConnectionError(
            f"Expected status code {EXPECTED_STATUS}, but got {response.status_code} for parent DOI {parent_doi}"
        )

    data = response.json()
    related_identifiers = data["data"]["attributes"].get("relatedIdentifiers", [])

    cleaned = [ri for ri in related_identifiers if ri.get("relationType") != "HasVersion"]
    additions = [
        {
            "relationType": "HasVersion",
            "relatedIdentifier": next(iter(d.keys())),
            "relatedIdentifierType": "DOI",
        }
        for d in relations
    ]

    new_related_identifiers = cleaned + additions
    data["data"]["attributes"]["relatedIdentifiers"] = new_related_identifiers

    doi_client.datacite_request(data, record, method="PUT", url=parent_doi_url)


def update_doi_relations(record: Record) -> None:
    """Update all datacite DOI relations."""
    parent_doi = get_parent_doi(record)
    if parent_doi:
        update_relations(record, parent_doi)
        update_parent_relations(record)
