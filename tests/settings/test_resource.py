#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for DOI settings resource."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from flask import g, request
from flask_resources.context import ResourceRequestCtx

from oarepo_doi.settings.resource import (
    CommunityDoiSettingsResource,
    CommunityDoiSettingsResourceConfig,
)


def _resource_context(config):
    """Create resource request context with a simple response handler."""
    ctx = ResourceRequestCtx(config)
    ctx.response_handler = SimpleNamespace(
        make_response=lambda data, code, many=False: (data, code),
    )
    return ctx


def test_read_service(app):
    """Read delegates to service and returns serialized item."""
    identity = SimpleNamespace(id="identity")
    item = SimpleNamespace(to_dict=Mock(return_value={"id": "settings-id"}))
    service = SimpleNamespace(read=Mock(return_value=item))
    config = CommunityDoiSettingsResourceConfig()
    resource = CommunityDoiSettingsResource(config, service)

    with app.test_request_context("/doi_settings/settings-id"), _resource_context(config):
        g.identity = identity
        request.view_args = {"id": "settings-id"}

        assert resource.read() == ({"id": "settings-id"}, 200)
        service.read.assert_called_once_with(id_="settings-id", identity=identity)


def test_update_service(app):
    """Update delegates request data to service."""
    identity = SimpleNamespace(id="identity")
    item = SimpleNamespace(to_dict=Mock(return_value={"id": "settings-id"}))
    service = SimpleNamespace(update=Mock(return_value=item))
    config = CommunityDoiSettingsResourceConfig()
    resource = CommunityDoiSettingsResource(config, service)

    with app.test_request_context(
        "/doi_settings/settings-id?expand=true",
        method="PUT",
        json={"prefix": "10.12345"},
        headers={"If-Match": "1"},
    ), _resource_context(config):
        g.identity = identity
        request.view_args = {"id": "settings-id"}

        assert resource.update() == ({"id": "settings-id"}, 200)
        service.update.assert_called_once_with(
            identity,
            "settings-id",
            {"prefix": "10.12345"},
            revision_id=1,
            expand=True,
        )


def test_delete_service(app):
    """Delete delegates to service and returns empty response."""
    identity = SimpleNamespace(id="identity")
    service = SimpleNamespace(delete=Mock())
    config = CommunityDoiSettingsResourceConfig()
    resource = CommunityDoiSettingsResource(config, service)

    with app.test_request_context(
        "/doi_settings/settings-id",
        method="DELETE",
        headers={"If-Match": "1"},
    ), _resource_context(config):
        g.identity = identity
        request.view_args = {"id": "settings-id"}

        assert resource.delete() == ("", 204)
        service.delete.assert_called_once_with(identity, "settings-id", revision_id=1)
