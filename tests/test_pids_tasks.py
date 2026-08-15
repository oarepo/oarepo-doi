#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""PID task-style tests for record-aware DataCite operations."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from invenio_rdm_records.services.pids.providers.datacite import DataCitePIDProvider


def test_api_uses_community_datacite_credentials(app, doi_client, doi_record):
    """The DataCite API client is built from the current record's community."""
    with patch("oarepo_doi.services.providers.client.DataCiteRESTClient") as datacite_rest_client:
        with doi_client.for_record(doi_record):
            assert doi_client.api is datacite_rest_client.return_value
        datacite_rest_client.assert_called_once_with(
            "community-user",
            "community-password",
            "10.12345",
            False,
        )


def test_update_sets_record_context_before_upstream_call(doi_provider, doi_record, doi_pid):
    """Updates bind the record before delegating to the upstream provider."""
    def update(self, pid, record, **kwargs: Any) -> str:
        assert self.client.record is record
        return "updated"

    with patch.object(DataCitePIDProvider, "update", autospec=True, side_effect=update):
        assert doi_provider.update(doi_pid, doi_record, url="https://example.org/r/1") == ("updated")


def test_restore_sets_record_context_before_upstream_call(doi_provider, doi_record, doi_pid):
    """Restore binds the task-provided record before upstream handling."""
    def restore(self, pid, **kwargs: Any) -> str:
        assert self.client.record is kwargs["record"]
        return "restored"

    with patch.object(DataCitePIDProvider, "restore", autospec=True, side_effect=restore):
        assert doi_provider.restore(doi_pid, record=doi_record) == "restored"


def test_delete_sets_record_context_before_upstream_call(doi_provider, doi_record, doi_pid):
    """Delete binds the task-provided record before upstream handling."""
    def delete(self, pid, **kwargs: Any) -> str:
        assert self.client.record is kwargs["record"]
        return "deleted"

    with patch.object(DataCitePIDProvider, "delete", autospec=True, side_effect=delete):
        assert doi_provider.delete(doi_pid, record=doi_record) == "deleted"
