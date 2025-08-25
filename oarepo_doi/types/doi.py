#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Request type for DOI management."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, cast, override

from flask import current_app
from marshmallow.exceptions import ValidationError
from oarepo_requests.types.generic import NonDuplicableOARepoRequestType
from oarepo_requests.types.ref_types import ModelRefTypes
from oarepo_requests.utils import classproperty, is_auto_approved, request_identity_matches
from oarepo_runtime.i18n import lazy_gettext as _

from ..actions.doi import (
    AssignDoiDeclineAction,
    CreateDoiAction,
    DeleteDoiAction,
    DeleteDoiDeclineAction,
    DeleteDoiSubmitAction,
    ValidateDataForDoiAction,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from flask_babel.speaklater import LazyString
    from flask_principal import Identity
    from invenio_records_resources.records import Record
    from invenio_requests.customizations.actions import RequestAction
    from invenio_requests.records.api import Request
    from oarepo_requests.typing import EntityReference

    from ..services.provider import OarepoDataCitePIDProvider


class DoiRequest(NonDuplicableOARepoRequestType):
    """Generic DOI request type."""

    @cached_property
    def provider(self) -> OarepoDataCitePIDProvider:
        """Return specific DOI provider."""
        providers: Iterable[Any] = current_app.config.get("RDM_PERSISTENT_IDENTIFIER_PROVIDERS") or ()
        for p in providers:
            if getattr(p, "name", None) == "datacite":
                return cast("OarepoDataCitePIDProvider", p)
        raise LookupError("Datacite provider not found in RDM_PERSISTENT_IDENTIFIER_PROVIDERS")


class DeleteDoiRequestType(DoiRequest):
    """Request type for DOI deletion."""

    type_id = "delete_doi"
    name = _("Cancel DOI registration")

    @classproperty
    def available_actions(self) -> dict[str, type[RequestAction]]:
        """Return available actions for the request type."""
        return {
            **super().available_actions,
            "accept": DeleteDoiAction,
            "submit": DeleteDoiSubmitAction,
            "decline": DeleteDoiDeclineAction,
        }

    description = _("Request for deletion of a registered DOI")
    receiver_can_be_none = True
    allowed_topic_ref_types = ModelRefTypes(published=False, draft=True)

    def is_applicable_to(self, identity: Identity, topic: Record, *args: Any, **kwargs: Any) -> Any:
        """Check if the request type is applicable to the topic."""
        if not self.provider.credentials(topic):  # no credentials for community and no default credentials
            return False
        doi_value = self.provider.get_doi_value(topic)
        pid_value = self.provider.get_pid_doi_value(topic)

        if pid_value is not None and pid_value.status.value == "R":
            return False

        # only make sense if there is registered doi
        # it is possible to cancel registration for only draft dois, which are associated only to record drafts.
        is_draft = getattr(topic, "is_draft", False)

        if doi_value and is_draft:
            return super().is_applicable_to(identity, topic, *args, **kwargs)
        return False

    @override
    def stateful_name(
        self,
        identity: Identity,
        *,
        topic: Record,
        request: Request | None = None,
        **kwargs: Any,
    ) -> str | LazyString:
        """Return the stateful name of the request."""
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
    def stateful_description(
        self,
        identity: Identity,
        *,
        topic: Record,
        request: Any | None = None,
        **kwargs: Any,
    ) -> str | LazyString:
        """Return the stateful description of the request."""
        description = _()

        if is_auto_approved(self, identity=identity, topic=topic):
            description = _("Click to cancel DOI registration.")

        if not request:
            description = _("Request permission to cancel DOI registration.")
        else:
            match request.status:
                case "submitted":
                    if request_identity_matches(request.created_by, identity):
                        description = _(
                            "Permission to cancel DOI registration requested. "
                            "You will be notified about the decision by email."
                        )
                    elif request_identity_matches(request.receiver, identity):
                        description = _(
                            "You have been asked to approve the request to cancel DOI registration to a record. "
                            "You can approve or reject the request."
                        )
                    else:
                        description = _("Permission to cancel DOI registration requested. ")
                case _:
                    if request_identity_matches(request.created_by, identity):
                        description = _("Submit request to get permission to cancel DOI registration.")
        return description


class AssignDoiRequestType(DoiRequest):
    """Request type for DOI registration."""

    type_id = "assign_doi"
    name = _("Assign DOI")

    @classproperty
    def available_actions(self) -> dict[str, type[RequestAction]]:
        """Return available actions for the request type."""
        return {
            **super().available_actions,
            "accept": CreateDoiAction,
            "submit": ValidateDataForDoiAction,
            "decline": AssignDoiDeclineAction,
        }

    description = _("Request for DOI assignment")
    receiver_can_be_none = True
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)

    def can_create(
        self,
        identity: Identity,
        data: dict,
        receiver: EntityReference,
        topic: Record,
        creator: EntityReference,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Check if the request can be created."""
        if not self.provider.credentials(topic):  # no credentials for community and no default credentials
            return False
        errors = self.provider.metadata_check(topic)
        if len(errors) > 0:
            raise ValidationError(message=errors)

        super().can_create(identity, data, receiver, topic, creator, *args, **kwargs)
        return False

    def is_applicable_to(self, identity: Identity, topic: Record, *args: Any, **kwargs: Any) -> Any:
        """Check if the request type is applicable to the topic."""
        if not self.provider.credentials(topic):  # no credentials for community and no default credentials
            return False
        mode = current_app.config.get("DATACITE_MODE")
        if mode in ("AUTOMATIC", "AUTOMATIC_DRAFT"):
            return False

        doi_value = self.provider.get_doi_value(topic)  # if ANY doi already assigned, adding another is not possible
        if doi_value is not None:
            return False
        return super().is_applicable_to(identity, topic, *args, **kwargs)

    @override
    def stateful_name(
        self,
        identity: Identity,
        *,
        topic: Record,
        request: Request | None = None,
        **kwargs: Any,
    ) -> str | LazyString:
        """Return the stateful name of the request."""
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
    def stateful_description(
        self,
        identity: Identity,
        *,
        topic: Record,
        request: Any | None = None,
        **kwargs: Any,
    ) -> str | LazyString:
        """Return the stateful description of the request."""
        description = _()
        if is_auto_approved(self, identity=identity, topic=topic):
            description = _("Click to assign DOI.")

        if not request:
            description = _("Request permission to assign DOI.")
        else:
            match request.status:
                case "submitted":
                    if request_identity_matches(request.created_by, identity):
                        description = _(
                            "Permission to assign DOI requested. You will be notified about the decision by email."
                        )
                    elif request_identity_matches(request.receiver, identity):
                        description = _(
                            "You have been asked to approve the request to assign DOI to a record. "
                            "You can approve or reject the request."
                        )
                    else:
                        description = _("Permission to assign DOI requested. ")
                case _:
                    if request_identity_matches(request.created_by, identity):
                        description = _("Submit request to get permission to assign DOI.")

        return description
