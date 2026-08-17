# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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
