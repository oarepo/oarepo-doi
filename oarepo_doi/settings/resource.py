#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI settings resource config."""

from __future__ import annotations

from typing import Any

import marshmallow as ma
from flask import g
from flask_resources import resource_requestctx, response_handler
from invenio_records_resources.resources import RecordResource, RecordResourceConfig
from invenio_records_resources.resources.errors import ErrorHandlersMixin
from invenio_records_resources.resources.records.resource import (
    request_data,
    request_extra_args,
    request_headers,
    request_view_args,
)


class CommunityDoiSettingsResourceConfig(RecordResourceConfig):
    """DOI settings resource configuration."""

    blueprint_name: str | None = "oarepo_doi_settings"
    url_prefix: str = "/doi_settings"  # pyright: ignore[reportIncompatibleVariableOverride]

    routes: Any = {  # noqa: RUF012
        "list": "",
        "item": "/<id>",
    }  # pyright: ignore[reportIncompatibleVariableOverride]

    request_view_args: Any = {  # noqa: RUF012
        "id": ma.fields.Str(),
    }  # pyright: ignore[reportIncompatibleVariableOverride]

    error_handlers: Any = {  # noqa: RUF012
        **ErrorHandlersMixin.error_handlers,
    }  # pyright: ignore[reportIncompatibleVariableOverride]

    response_handlers: Any = {  # noqa: RUF012
        "application/vnd.inveniordm.v1+json": RecordResourceConfig.response_handlers["application/json"],
        **RecordResourceConfig.response_handlers,
    }


class CommunityDoiSettingsResource(RecordResource):
    """DOI settings resource."""

    @request_view_args
    @response_handler()
    def read(self) -> Any:
        """Read a user."""
        item = self.service.read(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return item.to_dict(), 200

    @request_extra_args
    @request_headers
    @request_view_args
    @request_data
    @response_handler()
    def update(self) -> Any:
        """Update an item."""
        item = self.service.update(
            g.identity,
            resource_requestctx.view_args["id"],
            resource_requestctx.data,
            revision_id=resource_requestctx.headers.get("if_match"),
            expand=resource_requestctx.args.get("expand", False),
        )
        return item.to_dict(), 200

    @request_headers
    @request_view_args
    def delete(self) -> Any:
        """Delete an item."""
        self.service.delete(
            g.identity,
            resource_requestctx.view_args["id"],
            revision_id=resource_requestctx.headers.get("if_match"),
        )
        return "", 204
