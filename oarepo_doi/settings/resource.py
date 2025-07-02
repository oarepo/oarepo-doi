"""DOI settings resource config."""

import marshmallow as ma
from flask import g
from invenio_records_resources.resources import (
    RecordResource,
    RecordResourceConfig,
)
from invenio_records_resources.resources.errors import ErrorHandlersMixin
from invenio_records_resources.resources.records.resource import (
    request_view_args,
    request_extra_args,
    request_headers,
    request_data
)
from flask_resources import (

    resource_requestctx,
    response_handler,

)

class CommunityDoiSettingsResourceConfig(RecordResourceConfig):
    """DOI settings resource configuration."""

    blueprint_name = "oarepo_doi_settings"
    url_prefix = "/doi_settings"
    routes = {
        "list": "",
        "item": "/<id>",
    }

    request_view_args = {
        "id": ma.fields.Str(),
    }

    error_handlers = {
        **ErrorHandlersMixin.error_handlers,
    }

    response_handlers = {
        "application/vnd.inveniordm.v1+json": RecordResourceConfig.response_handlers[
            "application/json"
        ],
        **RecordResourceConfig.response_handlers,
    }


class CommunityDoiSettingsResource(RecordResource):

    @request_view_args
    @response_handler()
    def read(self):
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
    def update(self):
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
    def delete(self):
        """Delete an item."""
        self.service.delete(
            g.identity,
            resource_requestctx.view_args["id"],
            revision_id=resource_requestctx.headers.get("if_match"),
        )
        return "", 204