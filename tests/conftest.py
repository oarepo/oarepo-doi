import copy
import os
import yaml
import pytest

from flask_security.utils import  login_user
from invenio_access.permissions import system_identity
from invenio_accounts.testutils import login_user_via_session
from invenio_app.factory import create_api
from invenio_requests.customizations import CommentEventType, LogEventType
from thesis.proxies import current_service
from invenio_users_resources.records import UserAggregate

@pytest.fixture()
def default_workflow_json():
    return {"parent": {"workflow": "default"}}

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


class LoggedClient:
    def __init__(self, client, user_fixture):
        self.client = client
        self.user_fixture = user_fixture

    def _login(self):
        login_user(self.user_fixture.user, remember=True)
        login_user_via_session(self.client, email=self.user_fixture.email)

    def post(self, *args, **kwargs):
        self._login()
        return self.client.post(*args, **kwargs)

    def get(self, *args, **kwargs):
        self._login()
        return self.client.get(*args, **kwargs)

    def put(self, *args, **kwargs):
        self._login()
        return self.client.put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._login()
        return self.client.delete(*args, **kwargs)

@pytest.fixture()
def logged_client(client):
    def _logged_client(user):
        return LoggedClient(client, user)

    return _logged_client

@pytest.fixture()
def users(app, db, UserFixture):
    user1 = UserFixture(
        email="user1@example.org",
        password="password",
        active=True,
        confirmed=True,
    )
    user1.create(app, db)

    user2 = UserFixture(
        email="user2@example.org",
        password="beetlesmasher",
        active=True,
        confirmed=True,
    )
    user2.create(app, db)

    user3 = UserFixture(
        email="user3@example.org",
        password="beetlesmasher",
        active=True,
        confirmed=True,
    )
    user3.create(app, db)

    db.session.commit()
    UserAggregate.index.refresh()
    return [user1, user2, user3]

@pytest.fixture()
def urls():
    return {"BASE_URL": "/thesis/", "BASE_URL_REQUESTS": "/requests/"}

@pytest.fixture(scope="module")
def record_service():
    return current_service

@pytest.fixture()
def create_doi_data_function():
    def ret_data(record_id):
        return {
            "request_type": "create_doi",
            "topic": {"thesis_draft": record_id},
        }

    return ret_data

@pytest.fixture()
def record_factory(record_service, default_workflow_json):
    def record(identity, custom_workflow=None, additional_data=None):
        json = copy.deepcopy(default_workflow_json)
        if custom_workflow:  # specifying this assumes use of workflows
            json["parent"]["workflow"] = custom_workflow
        json = {
            "metadata": {
                "title": "Title",

            },
            **json,
        }
        if additional_data:
            json |= additional_data
        draft = record_service.create(identity, json)
        record = record_service.publish(system_identity, draft.id)
        return record._obj

    return record