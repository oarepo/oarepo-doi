import requests
from flask import current_app
from .utils import community_slug_for_credentials
from oarepo_doi.settings.models import CommunityDoiSettings
from typing import Any
from invenio_db import db

EXPECTED_STATUS = {
        "GET": [200],
        "POST": [200, 201],
        "PUT": [200, 204, 201],
        "DELETE": [200, 204, 404],
    }

class DOIClient:

    @property
    def url(self) -> Any:
        """Return datacite url."""
        return current_app.config.get("DATACITE_URL")

    def generate_doi(self,prefix, record):
        return f"{prefix}/{record['id']}"


    def credentials(self, record: Any) -> tuple[str, str, str] | None:
        """Return credentials."""
        if hasattr(record, "parent"):
            record = record.parent
        elif "parent" in record:
            record = record["parent"]
        slug = community_slug_for_credentials(record.get("communities", {}).get("default", None))
        if not slug:
            credentials = current_app.config.get("DATACITE_CREDENTIALS_DEFAULT", None)
        else:
            doi_settings = db.session.query(CommunityDoiSettings).filter_by(community_slug=slug).first()
            if doi_settings is None:
                credentials = current_app.config.get("DATACITE_CREDENTIALS_DEFAULT", None)
            else:
                credentials = doi_settings
        if credentials is None:
            return None
        if type(credentials) == dict:
            return credentials["username"], credentials["password"], credentials["prefix"]
        return credentials.username, credentials.password, credentials.prefix

    def datacite_request(self, data, record,doi, method, url = None):
        username, password, prefix = self.credentials(record)

        if not url:

            url = self.url.rstrip("/") + "/" + doi.replace("/", "%2F")

        response = requests.request(
            method=method.upper(),
            url=url,
            json=data,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
        )
        expected = EXPECTED_STATUS.get(method, [200])
        if response.status_code not in expected:
            raise requests.ConnectionError(
                f"Expected status code {expected}, but got {response.status_code}"
            )
        return response

