from oarepo_doi.services.doi_client import DOIClient
from oarepo_doi.services.doi_provider import DOIProvider
from .test_provider.mapping import TestMapping

def test_client(
    app,
    users,
    logged_client,
    draft_factory,
    submit_request_on_draft,
    link2testclient,
    urls,
):
    client = DOIClient()

    creator = users[0]
    draft = draft_factory(creator.identity)

    username, password, prefix = client.credentials(draft)
    assert username == "username"
    assert password == "password"
    assert prefix == "prefix"

    doi = client.generate_doi(prefix, draft)

    assert doi == f"prefix/{draft["id"]}"

def test_provider(
    app,
    users,
    logged_client,
    draft_factory,
    submit_request_on_draft,
    link2testclient,
    urls,
):
    provider = DOIProvider()

    creator = users[0]
    draft = draft_factory(creator.identity)

    mapping = provider.mapping
    assert mapping.__class__ == TestMapping
    doi_value = provider.get_doi_value(draft)

    assert doi_value is None


def test_mapping(
    app,
    users,
    logged_client,
    draft_factory,
    submit_request_on_draft,
    link2testclient,
    urls,
):
    creator = users[0]
    draft = draft_factory(creator.identity)

    provider = DOIProvider()
    mapping = provider.mapping
    errors = mapping.metadata_check(draft)

    assert errors == {'metadata.publishers': ['Missing data for required field.']}

    payload = mapping.create_datacite_payload(draft)
    assert payload == {'titles': 'blabla'}

