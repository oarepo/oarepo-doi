from oarepo_runtime.datastreams.utils import get_record_service_for_record
from invenio_access.permissions import system_identity
import requests
from flask import current_app
from .doi_client import DOIClient
def get_versions(record):
    topic_service = get_record_service_for_record(record)
    try:
        versions = topic_service.search_versions(
            identity=system_identity, id_=record.pid.pid_value, params={"size": 1000}
        )
        versions_hits = versions.to_dict()["hits"]["hits"]
    except:
        versions_hits = []
    return versions_hits

def get_doi_indices(record):
    versions = get_doi_versions(record)
    doi_indices = []
    for rec in versions:

        pids = rec.get("pids", {})
        doi = pids["doi"]["identifier"]
        doi_indices.append(doi)
    return doi_indices
def get_doi_versions(record):
    versions_hits = get_versions(record)
    existing_index = next((i for i, v in enumerate(versions_hits) if v.get("id") == record["id"]), None)

    if getattr(getattr(record, "deletion_status", None), "is_deleted", False):
        if existing_index is not None:
            del versions_hits[existing_index]
    else:
        if existing_index is None:
            versions_hits.append(record.dumps())
        else:
            versions_hits[existing_index] = record.dumps()

    doi_versions = []
    seen = set()
    for version in versions_hits:
        if "is_published" in version and version["is_published"]:
            pids = version.get("pids", {})
            versions = version.get("versions", {})
            if (
                    "doi" in pids
                    and "provider" in pids["doi"]
                    and pids["doi"]["provider"] == "datacite"
            ):
                doi = pids["doi"]["identifier"]
                if doi not in seen:
                    doi_versions.append(version)
                    seen.add(doi)

    doi_versions.sort(key=lambda v: v.get("versions", {}).get("index"))

    return doi_versions

def get_parent_doi(record):
    parent = record.parent
    pids = parent.get("pids", {})
    if (
            "doi" in pids
            and "provider" in pids["doi"]
            and pids["doi"]["provider"] == "datacite"
    ):
        return pids["doi"]["identifier"]

def get_latest(record):
    versions = get_doi_versions(record)
    if not versions:
        return None

    latest = versions[-1]

    return latest

def update_relations(record, relations, parent_doi):
    doi_client = DOIClient()

    sorted_dois = relations

    url = current_app.config["DATACITE_URL"]
    exclude = {"IsVersionOf", "IsPreviousVersionOf", "IsNewVersionOf"}

    for idx, doi in enumerate(sorted_dois):
        doi_url = url.rstrip("/") + "/" + doi.replace("/", "%2F")
        response = requests.get(
            url=doi_url,
        )

        data = response.json()

        related_identifiers = data["data"]["attributes"].get("relatedIdentifiers", {})

        cleaned = [
            ri for ri in related_identifiers
            if ri.get("relationType") not in exclude
            ]

        additions = []

        additions.append({
            "relationType": "IsVersionOf",
            "relatedIdentifier": parent_doi,
            "relatedIdentifierType": "DOI",
        })

        if idx > 0:
            prev_doi = sorted_dois[idx - 1]
            additions.append({
                "relationType": "IsNewVersionOf",
                "relatedIdentifier": prev_doi,
                "relatedIdentifierType": "DOI",
            })

        if idx < len(sorted_dois) - 1:
            next_doi = sorted_dois[idx + 1]
            additions.append({
                "relationType": "IsPreviousVersionOf",
                "relatedIdentifier": next_doi,
                "relatedIdentifierType": "DOI",
            })

        new_related_identifiers = cleaned + additions
        data["data"]["attributes"]["relatedIdentifiers"] = new_related_identifiers
        update_response = doi_client.datacite_request(data, record,doi, method="PUT", url=doi_url)

def update_parent_relations(record, relations, parent_doi):

    doi_client = DOIClient()

    url = current_app.config["DATACITE_URL"]
    parent_doi_url = url.rstrip("/") + "/" + parent_doi.replace("/", "%2F")

    response = requests.get(parent_doi_url)
    if response.status_code != 200:
        raise requests.ConnectionError(
            f"Expected status code 200, but got {response.status_code} for parent DOI {parent_doi}"
        )

    data = response.json()
    related_identifiers = data["data"]["attributes"].get("relatedIdentifiers", [])

    cleaned = [
        ri for ri in related_identifiers
        if ri.get("relationType") != "HasVersion"
    ]
    additions = [
        {
            "relationType": "HasVersion",
            "relatedIdentifier": d,
            "relatedIdentifierType": "DOI",
        }
        for d in relations
    ]

    new_related_identifiers = cleaned + additions
    data["data"]["attributes"]["relatedIdentifiers"] = new_related_identifiers

    doi_client.datacite_request(
        data, record,parent_doi, method="PUT", url=parent_doi_url
    )



def update_doi_relations(record):
    parent_doi = get_parent_doi(record)
    relations = get_doi_indices(record)
    if parent_doi:
        update_relations(record,relations, parent_doi)
        update_parent_relations(record,relations, parent_doi)