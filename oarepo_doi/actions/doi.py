from functools import cached_property
from typing import Any

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
from oarepo_doi.services.doi_provider import DOIProvider
from oarepo_doi.services.doi_client import DOIClient
from oarepo_doi.services.relations import update_doi_relations
from invenio_records_resources.services.uow import RecordIndexOp

from oarepo_runtime.datastreams.utils import get_record_service_for_record
class OarepoDoiActionMixin:
    @cached_property
    def provider(self):
        return DOIProvider()

    @property
    def client(self):
        return DOIClient()


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
        make_findable = True

        if topic.is_draft:
            make_findable = False

        self.provider.create(record=topic, make_findable=make_findable)
        if make_findable:
            created = self.provider.create_canonical(record=topic)
            if not created:
                self.provider.update_canonical(record=topic)

        update_doi_relations(topic)

        topic_service = get_record_service_for_record(topic)
        uow.register(RecordIndexOp(topic, indexer=topic_service.indexer, index_refresh=True))

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
        self.provider.delete(topic)
        #todo proc to neni potreba - protoze nikdy nebude publish
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
        errors = self.provider.mapping.metadata_check(topic)

        if len(errors) > 0:
            raise ValidationError(message=errors)
        uow.register(
            NotificationOp(
                AssignDoiRequestSubmitNotificationBuilder.build(request=self.request)
            )
        )
