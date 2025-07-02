from invenio_access.permissions import system_identity
from invenio_records_resources.services.records.schema import (
    BaseRecordSchema,
)
from marshmallow import fields

class  CommunityDoiSettingsSchema(BaseRecordSchema):
    username = fields.String(required=True)
    prefix =  fields.String(required=True)
    password =  fields.String(required=True)
    community_slug =  fields.String(required=True)

    class Meta:
        strict = True