from functools import cached_property
from typing import Any

from flask import current_app
from flask_principal import Identity
from invenio_notifications.services.uow import NotificationOp
from invenio_records_resources.services.uow import UnitOfWork
from marshmallow.exceptions import ValidationError
from oarepo_requests.actions.components import RequestActionState
from oarepo_requests.actions.generic import (
    OARepoAcceptAction,
    OARepoDeclineAction,
    OARepoSubmitAction,
)
from oarepo_runtime.i18n import lazy_gettext as _
from typing_extensions import override

from oarepo_doi.notifications.builders.assign_doi import (
    AssignDoiRequestAcceptNotificationBuilder,
    AssignDoiRequestDeclineNotificationBuilder,
    AssignDoiRequestSubmitNotificationBuilder,
)
from oarepo_doi.notifications.builders.delete_doi import (
    DeleteDoiRequestAcceptNotificationBuilder,
    DeleteDoiRequestDeclineNotificationBuilder,
    DeleteDoiRequestSubmitNotificationBuilder,
)


class OarepoDoiActionMixin:
    @cached_property
    def provider(self):
        providers = current_app.config.get("RDM_PERSISTENT_IDENTIFIER_PROVIDERS")

        for _provider in providers:
            if _provider.name == "datacite":
                provider = _provider
                break
        return provider


class AssignDoiAction(OARepoAcceptAction, OarepoDoiActionMixin):
    log_event = True


class CreateDoiAction(AssignDoiAction):

    @override
    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ):

        topic = self.request.topic.resolve()

        if topic.is_draft:
            self.provider.create_and_reserve(topic)
        else:
            self.provider.create_and_reserve(topic, event="publish")

        uow.register(
            NotificationOp(
                AssignDoiRequestAcceptNotificationBuilder.build(request=self.request)
            )
        )


class DeleteDoiAction(AssignDoiAction):

    @override
    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        topic = self.request.topic.resolve()

        """
        it is not allowed to delete DOI within the published record, the doi is changed to "registered" 
        by the component when deleting the published record
        """
        if topic.is_draft:
            self.provider.delete_draft(topic)

        uow.register(
            NotificationOp(
                DeleteDoiRequestAcceptNotificationBuilder.build(request=self.request)
            )
        )


class DeleteDoiSubmitAction(OARepoSubmitAction):

    @override
    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        topic = self.request.topic.resolve()

        uow.register(
            NotificationOp(
                DeleteDoiRequestSubmitNotificationBuilder.build(request=self.request)
            )
        )


class DeleteDoiDeclineAction(OARepoDeclineAction):

    @override
    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        topic = self.request.topic.resolve()

        uow.register(
            NotificationOp(
                DeleteDoiRequestDeclineNotificationBuilder.build(request=self.request)
            )
        )


class AssignDoiDeclineAction(OARepoDeclineAction):
    """Decline action for assign doi requests."""

    name = _("Return for correction")

    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ):
        uow.register(
            NotificationOp(
                AssignDoiRequestDeclineNotificationBuilder.build(request=self.request)
            )
        )
        return super().apply(identity, state, uow, *args, **kwargs)


class ValidateDataForDoiAction(OARepoSubmitAction, OarepoDoiActionMixin):
    log_event = True

    @override
    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        topic = self.request.topic.resolve()
        errors = self.provider.metadata_check(topic)

        if len(errors) > 0:
            raise ValidationError(message=errors)
        uow.register(
            NotificationOp(
                AssignDoiRequestSubmitNotificationBuilder.build(request=self.request)
            )
        )
