from flask import current_app
from marshmallow.exceptions import ValidationError
from oarepo_requests.actions.generic import OARepoAcceptAction, OARepoSubmitAction

from functools import cached_property

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


    def execute(self, identity, uow, *args, **kwargs):

        topic = self.request.topic.resolve()

        if topic.is_draft:
            self.provider.create_and_reserve(topic)
        else:
            self.provider.create_and_reserve(topic, event="publish")
        super().execute(identity, uow)

class DeleteDoiAction(AssignDoiAction):

    def execute(self, identity, uow, *args, **kwargs):
        topic = self.request.topic.resolve()

        self.provider.delete(topic)

        super().execute(identity, uow)

class RegisterDoiAction(AssignDoiAction):

    def execute(self, identity, uow, *args, **kwargs):
        topic = self.request.topic.resolve()

        self.provider.create_and_reserve(topic)

        super().execute(identity, uow)

class ValidateDataForDoiAction(OARepoSubmitAction, OarepoDoiActionMixin):
    log_event = True

    def execute(self, identity, uow, *args, **kwargs):
        topic = self.request.topic.resolve()
        errors = self.provider.metadata_check(topic)

        if len(errors) > 0:
            raise ValidationError(
                message=errors
            )

        super().execute(identity, uow)
