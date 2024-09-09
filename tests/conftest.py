import os

import pytest
import yaml
from flask_principal import Identity, Need, UserNeed
from flask_security.utils import hash_password, login_user
from invenio_access.models import ActionRoles
from invenio_access.permissions import superuser_access
from invenio_accounts.models import Role
from invenio_accounts.testutils import login_user_via_session
from invenio_app.factory import create_api
from invenio_requests.customizations import CommentEventType, LogEventType
from invenio_requests.proxies import current_request_type_registry, current_requests
from invenio_requests.records.api import Request, RequestEventFormat
from thesis.proxies import current_service
from thesis.records.api import ThesisRecord

# from thesis.proxies import current_service
# from thesis.records.api import ThesisRecord


@pytest.fixture(scope="function")
def sample_metadata_list():
    data_path = f"thesis/data/sample_data.yaml"
    docs = list(yaml.load_all(open(data_path), Loader=yaml.SafeLoader))
    return docs


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return create_api


@pytest.fixture(scope="module")
def app_config(app_config):
    app_config["REQUESTS_REGISTERED_EVENT_TYPES"] = [LogEventType(), CommentEventType()]
    app_config["SEARCH_HOSTS"] = [
        {
            "host": os.environ.get("OPENSEARCH_HOST", "localhost"),
            "port": os.environ.get("OPENSEARCH_PORT", "9200"),
        }
    ]
    app_config["JSONSCHEMAS_HOST"] = "localhost"
    app_config[
        "RECORDS_REFRESOLVER_CLS"
    ] = "invenio_records.resolver.InvenioRefResolver"
    app_config[
        "RECORDS_REFRESOLVER_STORE"
    ] = "invenio_jsonschemas.proxies.current_refresolver_store"
    app_config["CACHE_TYPE"] = "SimpleCache"
    app_config["DATACITE_PREFIX"] = "123456"

    return app_config


@pytest.fixture(scope="module")
def identity_simple():
    """Simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method="system_role", value="any_user"))
    i.provides.add(Need(method="system_role", value="authenticated_user"))
    return i


@pytest.fixture(scope="module")
def identity_simple_2():
    """Simple identity fixture."""
    i = Identity(2)
    i.provides.add(UserNeed(2))
    i.provides.add(Need(method="system_role", value="any_user"))
    i.provides.add(Need(method="system_role", value="authenticated_user"))
    return i


@pytest.fixture(scope="module")
def requests_service(app):
    """Request Factory fixture."""

    return current_requests.requests_service


@pytest.fixture(scope="module")
def request_events_service(app):
    """Request Factory fixture."""
    service = current_requests.request_events_service
    return service


@pytest.fixture()
def create_request(requests_service):
    """Request Factory fixture."""

    def _create_request(identity, input_data, receiver, request_type, **kwargs):
        """Create a request."""
        # Need to use the service to get the id
        item = requests_service.create(
            identity, input_data, request_type=request_type, receiver=receiver, **kwargs
        )
        return item._request

    return _create_request


@pytest.fixture()
def submit_request(create_request, requests_service, **kwargs):
    """Opened Request Factory fixture."""

    def _submit_request(identity, data, **kwargs):
        """Create and submit a request."""
        request = create_request(identity, input_data=data, **kwargs)
        id_ = request.id
        return requests_service.execute_action(identity, id_, "submit", data)._request

    return _submit_request


@pytest.fixture(scope="module")
def users(app):
    """Create example users."""
    # This is a convenient way to get a handle on db that, as opposed to the
    # fixture, won't cause a DB rollback after the test is run in order
    # to help with test performance (creating users is a module -if not higher-
    # concern)
    from invenio_db import db

    with db.session.begin_nested():
        datastore = app.extensions["security"].datastore

        su_role = Role(name="superuser-access")
        db.session.add(su_role)

        su_action_role = ActionRoles.create(action=superuser_access, role=su_role)
        db.session.add(su_action_role)

        user1 = datastore.create_user(
            email="user1@example.org", password=hash_password("password"), active=True
        )
        user2 = datastore.create_user(
            email="user2@example.org", password=hash_password("password"), active=True
        )
        admin = datastore.create_user(
            email="admin@example.org", password=hash_password("password"), active=True
        )
        admin.roles.append(su_role)

    db.session.commit()
    return [user1, user2, admin]


@pytest.fixture()
def client_with_login(client, users):
    """Log in a user to the client."""
    user = users[0]
    login_user(user)
    login_user_via_session(client, email=user.email)
    return client


@pytest.fixture(scope="function")
def request_record_input_data():
    """Input data to a Request record."""
    ret = {
        "title": "Doc1 approval",
        "payload": {
            "content": "Can you approve my document doc1 please?",
            "format": RequestEventFormat.HTML.value,
        },
    }
    return ret


@pytest.fixture(scope="module")
def record_service():
    return current_service


@pytest.fixture(scope="function")
def example_topic_draft(record_service, identity_simple):
    draft = record_service.create(identity_simple, {})
    return draft._obj


@pytest.fixture(scope="function")
def example_topic(record_service, identity_simple):
    draft = record_service.create(identity_simple, {})
    record = record_service.publish(identity_simple, draft.id)
    id_ = record.id
    record = ThesisRecord.pid.resolve(id_)
    return record


@pytest.fixture(scope="module")
def identity_creator(identity_simple):  # for readability
    return identity_simple


@pytest.fixture(scope="module")
def identity_receiver(identity_simple_2):  # for readability
    return identity_simple_2


@pytest.fixture(scope="function")
def request_with_receiver_user(
    requests_service, example_topic, identity_creator, users
):
    receiver = users[1]
    type_ = current_request_type_registry.lookup("generic_request", quiet=True)
    request_item = requests_service.create(
        identity_creator, {}, type_, receiver=receiver, topic=example_topic
    )
    request = Request.get_record(request_item.id)
    return request_item
