from flask import current_app
from marshmallow.exceptions import ValidationError
from oarepo_requests.actions.generic import OARepoAcceptAction, OARepoSubmitAction, OARepoDeclineAction, AddTopicLinksOnPayloadMixin
from oarepo_runtime.i18n import lazy_gettext as _
from functools import cached_property
from typing_extensions import override
from flask_principal import Identity
from oarepo_requests.actions.components import RequestActionState
from invenio_records_resources.services.uow import UnitOfWork
from typing import Any
from invenio_notifications.services.uow import NotificationOp
from oarepo_doi.notifications.builders.assign_doi import (AssignDoiRequestSubmitNotificationBuilder,
                                                          AssignDoiRequestAcceptNotificationBuilder,
                                                          AssignDoiRequestDeclineNotificationBuilder
                                                          )
from oarepo_doi.notifications.builders.delete_doi import (DeleteDoiRequestSubmitNotificationBuilder,
                                                          DeleteDoiRequestAcceptNotificationBuilder,
                                                          DeleteDoiRequestDeclineNotificationBuilder
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
                AssignDoiRequestAcceptNotificationBuilder.build(
                    request=self.request
                )
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

        self.provider.delete(topic)
        uow.register(
            NotificationOp(
                DeleteDoiRequestAcceptNotificationBuilder.build(
                    request=self.request
                )
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
                DeleteDoiRequestSubmitNotificationBuilder.build(
                    request=self.request
                )
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
                DeleteDoiRequestDeclineNotificationBuilder.build(
                    request=self.request
                )
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
                AssignDoiRequestDeclineNotificationBuilder.build(
                    request=self.request
                )
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
            raise ValidationError(
                message=errors
            )
        uow.register(
            NotificationOp(
                AssignDoiRequestSubmitNotificationBuilder.build(
                    request=self.request
                )
            )
        )

