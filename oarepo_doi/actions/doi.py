from flask import current_app
from marshmallow.exceptions import ValidationError
from oarepo_requests.actions.generic import OARepoAcceptAction, OARepoSubmitAction

from functools import cached_property
from typing_extensions import override
from flask_principal import Identity
from oarepo_requests.actions.components import RequestActionState
from invenio_records_resources.services.uow import UnitOfWork
from typing import Any
import importlib_metadata
from flask import current_app


class OarepoDoiActionMixin:
    def provider(self, topic):

        for x in importlib_metadata.entry_points(
                group='invenio_base.apps'
        ):
            if x.name == "oarepo_rdm":
                rdm = x.load()
                break
        service_id = rdm(app=current_app).record_service_from_pid_type(topic.pid.pid_type, topic.is_draft).id
        providers = current_app.config.get("RDM_PERSISTENT_IDENTIFIER_PROVIDERS")

        for _provider in providers:
            if _provider.name == "datacite":
                provider = _provider
                break
        provider.service_id = service_id
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
    ) -> None:

        topic = self.request.topic.resolve()

        if topic.is_draft:
            self.provider(topic).create_and_reserve(topic)
        else:
            self.provider(topic).create_and_reserve(topic, event="publish")

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

        self.provider(topic).delete(topic)


class RegisterDoiAction(AssignDoiAction):

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

        self.provider(topic).create_and_reserve(topic)


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
        errors = self.provider(topic).metadata_check(topic)

        if len(errors) > 0:
            raise ValidationError(
                message=errors
            )

