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

from types import SimpleNamespace
from unittest.mock import patch

from invenio_rdm_records.services.pids.providers.datacite import DataCitePIDProvider


def test_api_uses_community_datacite_credentials(app, doi_client, doi_record):
    """The DataCite API client is built from the current record's community."""
    with patch("oarepo_doi.services.providers.client.DataCiteRESTClient") as datacite_rest_client:
        doi_client.for_record(doi_record)

        assert doi_client.api is datacite_rest_client.return_value
        datacite_rest_client.assert_called_once_with(
            "community-user",
            "community-password",
            "10.12345",
            False,
        )


def test_register_sets_record_context_before_upstream_call(doi_provider, doi_record):
    """Registration binds the record before delegating to the upstream provider."""
    pid = SimpleNamespace(pid_value="10.12345/abcde-fghij")

    def register(self, pid, record, **kwargs):
        assert self.client.record is record
        return "registered"

    with patch.object(DataCitePIDProvider, "register", autospec=True, side_effect=register) as register_mock:
        assert doi_provider.register(pid, doi_record, url="https://example.org/r/1") == ("registered")
        register_mock.assert_called_once_with(doi_provider, pid, doi_record, url="https://example.org/r/1")


def test_update_sets_record_context_before_upstream_call(doi_provider, doi_record):
    """Updates bind the record before delegating to the upstream provider."""
    pid = SimpleNamespace(pid_value="10.12345/abcde-fghij")

    def update(self, pid, record, **kwargs):
        assert self.client.record is record
        return "updated"

    with patch.object(DataCitePIDProvider, "update", autospec=True, side_effect=update) as update_mock:
        assert doi_provider.update(pid, doi_record, url="https://example.org/r/1") == ("updated")
        update_mock.assert_called_once_with(doi_provider, pid, doi_record, url="https://example.org/r/1")


def test_restore_sets_record_context_before_upstream_call(doi_provider, doi_record):
    """Restore binds the task-provided record before upstream handling."""
    pid = SimpleNamespace(pid_value="10.12345/abcde-fghij")

    def restore(self, pid, **kwargs):
        assert self.client.record is kwargs["record"]
        return "restored"

    with patch.object(DataCitePIDProvider, "restore", autospec=True, side_effect=restore) as restore_mock:
        assert doi_provider.restore(pid, record=doi_record) == "restored"
        restore_mock.assert_called_once_with(doi_provider, pid, record=doi_record)


def test_delete_sets_record_context_before_upstream_call(doi_provider, doi_record):
    """Delete binds the task-provided record before upstream handling."""
    pid = SimpleNamespace(pid_value="10.12345/abcde-fghij")

    def delete(self, pid, **kwargs):
        assert self.client.record is kwargs["record"]
        return "deleted"

    with patch.object(DataCitePIDProvider, "delete", autospec=True, side_effect=delete) as delete_mock:
        assert doi_provider.delete(pid, record=doi_record) == "deleted"
        delete_mock.assert_called_once_with(doi_provider, pid, record=doi_record)
