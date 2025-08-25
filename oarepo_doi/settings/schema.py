#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Enhancements to the request schema."""

from __future__ import annotations

from invenio_records_resources.services.records.schema import BaseRecordSchema
from marshmallow import fields


class CommunityDoiSettingsSchema(BaseRecordSchema):
    """DOI setting schema."""

    username = fields.String(required=True)
    prefix = fields.String(required=True)
    password = fields.String(required=True)
    community_slug = fields.String(required=True)

    class Meta:
        """Metadata class."""

        strict = True
