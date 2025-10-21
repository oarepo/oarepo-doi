#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI oarepo client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests
from flask import current_app
from invenio_db import db
from marshmallow.exceptions import ValidationError

from oarepo_doi.settings.models import CommunityDoiSettings

from .utils import community_slug_for_credentials

if TYPE_CHECKING:
    from invenio_records.api import Record
EXPECTED_STATUS = {
    "GET": [200],
    "POST": [200, 201],
    "PUT": [200, 204, 201],
    "DELETE": [200, 204, 404],
}


class DOIClient:
    """DOI oarepo client."""

    @property
    def url(self) -> Any:
        """Return datacite url."""
        return current_app.config.get("DATACITE_URL")

    def generate_doi(self, prefix: str, record: Record) -> str:
        """Generate DOI."""
        return f"{prefix}/{record['id']}"

    def credentials(self, record: Any) -> tuple[str, str, str] | None:
        """Return credentials."""
        if hasattr(record, "parent"):
            record = record.parent
        elif "parent" in record:
            record = record["parent"]
        slug = community_slug_for_credentials(record["communities"].get("default", None))
        if not slug:
            credentials = current_app.config.get("DATACITE_CREDENTIALS_DEFAULT", None)
        else:
            doi_settings = db.session.query(CommunityDoiSettings).filter_by(community_slug=slug).first()
            if doi_settings is None:
                credentials = current_app.config.get("DATACITE_CREDENTIALS_DEFAULT", None)
            else:
                credentials = doi_settings
        if credentials is None:
            raise ValidationError(message="No credentials provided.")

        return credentials.username, credentials.password, credentials.prefix

    def datacite_request(self, data: dict, record: Record, method: str, url: str | None = None) -> Any:
        """Create request."""
        credentials = self.credentials(record)
        if credentials is None:
            return False
        username, password, prefix = credentials
        if not url:
            doi = self.generate_doi(prefix, record)

            url = self.url.rstrip("/") + "/" + doi.replace("/", "%2F")

        response = requests.request(
            method=method.upper(),
            url=url,
            json=data,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(username, password),
            timeout=20,
        )
        expected = EXPECTED_STATUS.get(method, [200])
        if response.status_code not in expected:
            raise requests.ConnectionError(f"Expected status code {expected}, but got {response.status_code}")
        return response
