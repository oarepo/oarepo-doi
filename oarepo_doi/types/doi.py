from flask import current_app
from invenio_base.utils import obj_or_import_string
from marshmallow.exceptions import ValidationError
from oarepo_requests.types.generic import NonDuplicableOARepoRequestType
from oarepo_requests.types.ref_types import ModelRefTypes
from oarepo_runtime.i18n import lazy_gettext as _
from typing_extensions import override
from oarepo_requests.utils import is_auto_approved, request_identity_matches
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

    description = _("Request for DOI assignment")
    receiver_can_be_none = True
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        mapping_file = current_app.config.get("DATACITE_MAPPING")
        mapping = obj_or_import_string(mapping_file[topic.schema])()
        errors = mapping.metadata_check(topic)
        if len(errors) > 0:
            raise ValidationError(
                message=errors
            )
        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)

    def is_applicable_to(self, identity, topic, *args, **kwargs):
        mapping_file = current_app.config.get("DATACITE_MAPPING")
        mapping = obj_or_import_string(mapping_file[topic.schema])()
        doi_value = mapping.get_doi(topic) #if ANY doi already assigned, adding another is not possible
        if doi_value:
            return False
        else:
            return super().is_applicable_to(identity, topic, *args, **kwargs)

    @override
    def stateful_name(self, identity, *, topic, request=None, **kwargs):
        if is_auto_approved(self, identity=identity, topic=topic):
            return self.name
        if not request:
            return _("Request DOI assignment")
        match request.status:
            case "submitted":
                return _("DOI assignment requested")
            case _:
                return _("Request DOI assignment")

    @override
    def stateful_description(self, identity, *, topic, request=None, **kwargs):
        if is_auto_approved(self, identity=identity, topic=topic):
            return _("Click to assign DOI.")

        if not request:
            return _("Request permission to assign DOI.")
        match request.status:
            case "submitted":
                if request_identity_matches(request.created_by, identity):
                    return _(
                        "Permission to assign DOI requested. "
                        "You will be notified about the decision by email."
                    )
                if request_identity_matches(request.receiver, identity):
                    return _(
                        "You have been asked to approve the request to assign DOI to a record. "
                        "You can approve or reject the request."
                    )
                return _("Permission to assign DOI requested. ")
            case _:
                if request_identity_matches(request.created_by, identity):
                    return _("Submit request to get permission to assign DOI.")