#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Pytest fixtures for OARepo DOI tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask

from oarepo_doi.services.providers.client import DataCiteRecordAwareClient
from oarepo_doi.services.providers.provider import DataCiteRecordAwareProvider


@pytest.fixture
def app():
    """Minimal app context for DataCite client configuration."""
    app = Flask("oarepo-doi-tests")
    with app.app_context():
        yield app


@pytest.fixture
def doi_record():
    """Record-like object with the fields used by the DOI client."""

    class Record(dict):
        """Small record double supporting both mapping and attribute access."""

        pid = SimpleNamespace(
            pid_value="abcde-fghijk",
            is_registered=lambda: True,
            register=lambda: True,
        )

    return Record(communities={"default": "test-community"}, access={"record": "public"})


@pytest.fixture
def doi_record_settings():
    """Community DOI settings used by the record-aware client."""
    return SimpleNamespace(
        prefix="10.12345",
        username="community-user",
        password="community-password",  # noqa: S106
    )


@pytest.fixture
def doi_client(app, doi_record_settings, monkeypatch):
    """Record-aware DataCite client with community settings mocked."""
    client = DataCiteRecordAwareClient(
        "datacite",
        config_overrides={
            "DATACITE_PREFIX": "10.99999",
            "DATACITE_USERNAME": "global-user",
            "DATACITE_PASSWORD": "global-password",
            "DATACITE_TEST_MODE": False,
        },
    )
    monkeypatch.setattr(client, "get_doi_settings", lambda record: doi_record_settings)  # noqa: ARG005
    return client


@pytest.fixture
def doi_provider(doi_client):
    """Record-aware DataCite PID provider."""
    return DataCiteRecordAwareProvider("datacite", client=doi_client)
