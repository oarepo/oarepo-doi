#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""PID service-style tests for the record-aware DataCite provider."""

from __future__ import annotations

import pytest

from oarepo_doi.services.providers.client import DataCiteRecordAwareClient
from oarepo_doi.services.providers.provider import DataCiteRecordAwareProvider


def test_generate_id_uses_community_doi_settings(doi_provider, doi_record):
    """The provider delegates DOI generation to a record-bound client."""
    doi = doi_provider.generate_id(doi_record)

    assert doi == "10.12345/abcde-fghij"
    assert doi_provider.client.record is doi_record


def test_generate_doi_falls_back_to_global_datacite_config(
    app, monkeypatch, doi_record
):
    """Without community settings the client behaves like the upstream client."""
    client = DataCiteRecordAwareClient("datacite")
    monkeypatch.setattr(client, "get_doi_settings", lambda record: None)
    app.config.update(
        DATACITE_PREFIX="10.99999",
        DATACITE_USERNAME="global-user",
        DATACITE_PASSWORD="global-password",
        DATACITE_FORMAT="{prefix}/global.{id}",
    )

    doi = client.generate_doi(doi_record)

    assert doi == "10.99999/global.abcde-fghij"


def test_generate_id_requires_configured_client(doi_record):
    """Record-aware provider fails explicitly when no client is configured."""
    provider = DataCiteRecordAwareProvider("datacite")
    provider.client = None

    with pytest.raises(RuntimeError, match="DataCite client is not configured"):
        provider.generate_id(doi_record)
