from functools import cached_property

from flask import current_app
from marshmallow.exceptions import ValidationError
from oarepo_requests.actions.generic import OARepoSubmitAction
from oarepo_requests.types.generic import NonDuplicableOARepoRequestType
from oarepo_requests.types.ref_types import ModelRefTypes
from oarepo_requests.utils import is_auto_approved, request_identity_matches
from oarepo_runtime.i18n import lazy_gettext as _
from typing_extensions import override

from ..actions.doi import CreateDoiAction, DeleteDoiAction, ValidateDataForDoiAction, AssignDoiDeclineAction, DeleteDoiDeclineAction, DeleteDoiSubmitAction


class DoiRequest(NonDuplicableOARepoRequestType):

    @cached_property
    def provider(self):
        providers = current_app.config.get("RDM_PERSISTENT_IDENTIFIER_PROVIDERS")

        for _provider in providers:
            if _provider.name == "datacite":
                provider = _provider
                break
        return provider


class DeleteDoiRequestType(DoiRequest):
    type_id = "delete_doi"
    name = _("Cancel DOI registration")

    @classmethod
    @property
    def available_actions(cls):
        return {
            **super().available_actions,
            "accept": DeleteDoiAction,
            "submit": DeleteDoiSubmitAction,
            "decline": DeleteDoiDeclineAction,
        }

    description = _("Request for deletion of a registered DOI")
    receiver_can_be_none = True
    allowed_topic_ref_types = ModelRefTypes(published=False, draft=True)

    def is_applicable_to(self, identity, topic, *args, **kwargs):
        if not self.provider.credentials(topic): #no credentials for community and no default credentials
            return False
        doi_value = self.provider.get_doi_value(topic)
        pid_value = self.provider.get_pid_doi_value(topic)


        if pid_value is not None and pid_value.status.value == "R":
            return False

        # only make sense if there is registered doi
        # it is possible to cancel registration for only draft dois, which are associated only to record drafts.
        if doi_value and topic.is_draft and getattr(topic, "is_draft", False):
            return super().is_applicable_to(identity, topic, *args, **kwargs)
        else:
            return False

    @override
    def stateful_name(self, identity, *, topic, request=None, **kwargs):
        if is_auto_approved(self, identity=identity, topic=topic):
            return self.name
        if not request:
            return _("Request DOI cancellation")
        match request.status:
            case "submitted":
                return _("DOI cancellation requested")
            case _:
                return _("Request DOI cancellation")

    @override
    def stateful_description(self, identity, *, topic, request=None, **kwargs):
        if is_auto_approved(self, identity=identity, topic=topic):
            return _("Click to cancel DOI registration.")

        if not request:
            return _("Request permission to cancel DOI registration.")
        match request.status:
            case "submitted":
                if request_identity_matches(request.created_by, identity):
                    return _(
                        "Permission to cancel DOI registration requested. "
                        "You will be notified about the decision by email."
                    )
                if request_identity_matches(request.receiver, identity):
                    return _(
                        "You have been asked to approve the request to cancel DOI registration to a record. "
                        "You can approve or reject the request."
                    )
                return _("Permission to cancel DOI registration requested. ")
            case _:
                if request_identity_matches(request.created_by, identity):
                    return _(
                        "Submit request to get permission to cancel DOI registration."
                    )


class AssignDoiRequestType(DoiRequest):
    type_id = "assign_doi"
    name = _("Assign DOI")

    @classmethod
    @property
    def available_actions(cls):
        return {
            **super().available_actions,
            "accept": CreateDoiAction,
            "submit": ValidateDataForDoiAction,
            "decline": AssignDoiDeclineAction
        }

    description = _("Request for DOI assignment")
    receiver_can_be_none = True
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)

    def can_create(self, identity, data, receiver, topic, creator, *args, **kwargs):
        if not self.provider.credentials(topic): #no credentials for community and no default credentials
            return False
        errors = self.provider.metadata_check(topic)
        if len(errors) > 0:
            raise ValidationError(message=errors)

        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)

    def is_applicable_to(self, identity, topic, *args, **kwargs):
        if not self.provider.credentials(topic):  # no credentials for community and no default credentials
            return False
        mode = current_app.config.get("DATACITE_MODE")
        if mode == "AUTOMATIC" or mode == "AUTOMATIC_DRAFT":
            return False

        doi_value = self.provider.get_doi_value(
            topic
        )  # if ANY doi already assigned, adding another is not possible
        if doi_value is not None:
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
