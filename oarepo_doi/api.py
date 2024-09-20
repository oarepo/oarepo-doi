import json
import uuid

import requests
from invenio_access.permissions import system_identity
from invenio_base.utils import obj_or_import_string
from invenio_communities import current_communities
from invenio_search.engine import dsl
from marshmallow.exceptions import ValidationError
from oarepo_runtime.datastreams.utils import get_record_service_for_record


def create_doi(service, record, data, event=None):
    """if event = None, doi will be created as a draft."""

    mapping = obj_or_import_string(service.mapping[record.schema])()
    errors = mapping.metadata_check(record)
    record_service = get_record_service_for_record(record)
    record["links"] = record_service.links_item_tpl.expand(system_identity, record)

    if len(errors) > 0 and event:
        raise ValidationError(
            message=f"Could not assigned doi due to validation error: {errors} "
        )
    request_metadata = {"data": {"type": "dois", "attributes": {}}}

    payload = mapping.create_datacite_payload(data)
    request_metadata["data"]["attributes"] = payload
    if service.specified_doi:
        doi = f"{service.prefix}/{record['id']}"
        request_metadata["data"]["attributes"]["doi"] = doi
    if event:
        request_metadata["data"]["attributes"]["event"] = event

    request_metadata["data"]["attributes"]["prefix"] = str(service.prefix)

    request = requests.post(
        url=service.url,
        json=request_metadata,
        headers={"Content-type": "application/vnd.api+json"},
        auth=(service.username, service.password),
    )

    if request.status_code != 201:
        raise requests.ConnectionError(
            "Expected status code 201, but got {}".format(request.status_code)
        )

    content = request.content.decode("utf-8")
    json_content = json.loads(content)
    doi_value = json_content["data"]["id"]
    mapping.add_doi(record, data, doi_value)


def edit_doi(service, record, event=None):
    """edit existing draft"""

    mapping = obj_or_import_string(service.mapping[record.schema])()
    doi_value = mapping.get_doi(record)

    if doi_value:
        errors = mapping.metadata_check(record)
        record_service = get_record_service_for_record(record)
        record["links"] = record_service.links_item_tpl.expand(system_identity, record)
        if len(errors) > 0 and event:
            raise ValidationError(
                message=f"Could not assigned doi due to validation error: {errors} "
            )
        if not service.url.endswith("/"):
            url = service.url + "/"
        else:
            url = service.url
        url = url + doi_value.replace("/", "%2F")

        request_metadata = mapping.create_datacite_payload(record)
        if event:
            request_metadata["data"]["attributes"]["event"] = event

        request = requests.put(
            url=url,
            json=request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(service.username, service.password),
        )

        if request.status_code != 200:
            raise requests.ConnectionError(
                "Expected status code 200, but got {}".format(request.status_code)
            )


def community_slug_for_credentials(value):
    if not value:
        return None
    id_value = None
    slug = None
    try:
        id_value = uuid.UUID(value, version=4)
    except:
        slug = value
    if not slug:
        search = current_communities.service._search(
            "search",
            system_identity,
            {},
            None,
            extra_filter=dsl.Q("term", **{"id": value}),
        )
        community = search.execute()
        c = list(community.hits.hits)[0]
        return c._source.slug
    return slug
