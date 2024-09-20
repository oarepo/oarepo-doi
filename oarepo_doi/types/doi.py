from flask import current_app
from invenio_base.utils import obj_or_import_string
from marshmallow.exceptions import ValidationError
from oarepo_requests.types.generic import NonDuplicableOARepoRequestType
from oarepo_requests.types.ref_types import ModelRefTypes
from oarepo_runtime.i18n import lazy_gettext as _

from ..actions.doi import CreateDoiAction, ValidateDataForDoiAction


class AssignDoiRequestType(NonDuplicableOARepoRequestType):
    type_id = "assign_doi"
    name = _("Assign Doi")

    @classmethod
    @property
    def available_actions(cls):
        return {
            **super().available_actions,
            "accept": CreateDoiAction,
            "submit": ValidateDataForDoiAction,
        }

    receiver_can_be_none = True
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        mapping_file = current_app.config.get("DATACITE_MAPPING")
        mapping = obj_or_import_string(mapping_file[topic.schema])()
        errors = mapping.metadata_check(topic)
        if len(errors) > 0:
            raise ValidationError(
                message=f"Could not assigned doi due to validation error: {errors} "
            )
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)

    def can_possibly_create(self, identity, record , *args, **kwargs):
        mapping_file = current_app.config.get("DATACITE_MAPPING")
        mapping = obj_or_import_string(mapping_file[record.schema])()
        doi_value = mapping.get_doi(record)
        if doi_value:
            return False
        else:
            return super().can_possibly_create(identity, record, *args, **kwargs)
