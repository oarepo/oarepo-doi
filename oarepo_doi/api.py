import requests
import json
from invenio_base.utils import obj_or_import_string
from flask import current_app


def create_doi(service, record, data, event = None ):
    """ if event = None, doi will be created as a draft."""

    mapping = obj_or_import_string(service.mapping[record.schema])()
    errors = mapping.metadata_check(data)
    if len(errors) > 0 and event:
        return #todo: dois can not be published with missing mandatory values

    request_metadata = mapping.create_datacite_payload(data)

    if event:
        request_metadata["data"]["attributes"]["event"] = event

    request_metadata["data"]["attributes"]["prefix"] = service.prefix

    request = requests.post(url=service.url, json=request_metadata, headers={'Content-type': 'application/vnd.api+json'},
                            auth=(service.username, service.password)
                            )

    if request.status_code != 201:
        raise requests.ConnectionError("Expected status code 201, but got {}".format(request.status_code))

    content = request.content.decode('utf-8')
    json_content = json.loads(content)
    doi_value = json_content['data']['id']
    mapping.add_doi(record, data, doi_value)


def edit_doi(service, record, event = None):
    """ edit existing draft """

    mapping = obj_or_import_string(service.mapping[record.schema])()
    errors = mapping.metadata_check(record)
    if len(errors) > 0 and event:
        return #todo: dois can not be published with missing mandatory values
    doi_value = mapping.get_doi(record)
    if doi_value:
        if not service.url.endswith('/'):
            url = service.url + '/'
        else:
            url = service.url
        url = url + doi_value.replace("/", "%2F")

        request_metadata = mapping.create_datacite_payload(record)
        if event:
            request_metadata["data"]["attributes"]["event"] = event

        request = requests.put(url=url, json=request_metadata, headers={'Content-type': 'application/vnd.api+json'},
                    auth=(service.username, service.password))

        if request.status_code != 200:
            raise requests.ConnectionError("Expected status code 200, but got {}".format(request.status_code))

