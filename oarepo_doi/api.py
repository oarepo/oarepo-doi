import json
import uuid
import requests

from invenio_access.permissions import system_identity
from invenio_base.utils import obj_or_import_string
from invenio_communities import current_communities
from invenio_db import db
from invenio_pidstore.providers.base import BaseProvider
from invenio_search.engine import dsl
from marshmallow.exceptions import ValidationError
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier

def create_doi(service, record, data, event=None):
    """if event = None, doi will be created as a draft."""

    mapping = obj_or_import_string(service.mapping[record.schema])()
    doi_value = mapping.get_doi(record)
    if doi_value:
        raise ValidationError(
            message="DOI already associated with the record."
        )
    errors = mapping.metadata_check(record)
    record_service = get_record_service_for_record(record)
    record["links"] = record_service.links_item_tpl.expand(system_identity, record)

    if len(errors) > 0 and event:
        raise ValidationError(
            message=errors
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

    if event:
        pid_status = 'R' #registred
    else: pid_status = 'K' #reserved
    BaseProvider.create('doi', doi_value, 'rec', record.id, pid_status)
    db.session.commit()


def edit_doi(service, record, event=None):
    """edit existing draft"""

    mapping = obj_or_import_string(service.mapping[record.schema])()
    doi_value = mapping.get_doi(record)
    if not check_if_correct_doi(doi_value, record):
        return
    if doi_value:
        errors = mapping.metadata_check(record)
        record_service = get_record_service_for_record(record)
        record["links"] = record_service.links_item_tpl.expand(system_identity, record)
        if len(errors) > 0 and event:
            raise ValidationError(
                message=errors
            )
        if not service.url.endswith("/"):
            url = service.url + "/"
        else:
            url = service.url
        url = url + doi_value.replace("/", "%2F")

        request_metadata = {"data": {"type": "dois", "attributes": {}}}
        payload = mapping.create_datacite_payload(record)
        request_metadata["data"]["attributes"] = payload

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

def check_if_correct_doi(value, record):
    try:
        doi = PersistentIdentifier.get_by_object('doi', "rec", record.id) #object has no doi in database == doi was added via created form by user
        if doi and not value: #doi deleted by user
            raise ValidationError(
                message="Datacite doi deleted by the user."
            )
    except PIDDoesNotExistError as e:
        return False
    try:
        doi = BaseProvider.get( value,'doi')
        return True
    except PIDDoesNotExistError as e:
        raise ValidationError(
            message="Datacite doi updated by the user."
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
