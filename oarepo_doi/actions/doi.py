#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI request actions."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, override

from invenio_notifications.services.uow import NotificationOp
from marshmallow.exceptions import ValidationError
from oarepo_requests.actions.generic import (
    OARepoAcceptAction,
    OARepoDeclineAction,
    OARepoSubmitAction,
)
from oarepo_runtime.i18n import lazy_gettext as _

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
from oarepo_doi.services.doi_client import DOIClient
from oarepo_doi.services.doi_provider import DOIProvider
from oarepo_doi.services.relations import update_doi_relations

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records_resources.services.uow import UnitOfWork
    from oarepo_requests.actions.components import RequestActionState


class OarepoDoiActionMixin:
    """Mixin for DOI actions."""

    @cached_property
    def provider(self) -> DOIProvider:
        """Return DOI provider."""
        return DOIProvider()

    @property
    def client(self) -> DOIClient:
        """Return DOI client."""
        return DOIClient()


class AssignDoiAction(OARepoAcceptAction, OarepoDoiActionMixin):
    """Assign DOI generic action."""

    log_event = True


class CreateDoiAction(AssignDoiAction):
    """Create DOI generic action."""

    @override
    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Create DOI."""
        topic = self.request.topic.resolve()
        doi_value = self.provider.get_doi_value(topic)
        new = True
        publish = True
        if doi_value:
            new = False
        if topic.is_draft:
            publish = False
        self.provider.create(record=topic, new=new, publish=publish)
        if publish:
            self.provider.create_canonical(record=topic, new=True)
        update_doi_relations(topic)

        uow.register(NotificationOp(AssignDoiRequestAcceptNotificationBuilder.build(request=self.request)))


class DeleteDoiAction(AssignDoiAction):
    """Delete DOI generic action."""

    @override
    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Delete DOI."""
        topic = self.request.topic.resolve()
        self.provider.delete(topic)
        uow.register(NotificationOp(DeleteDoiRequestAcceptNotificationBuilder.build(request=self.request)))


class DeleteDoiSubmitAction(OARepoSubmitAction):
    """Delete DOI submit action."""

    @override
    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Submit DOI deletion."""
        self.request.topic.resolve()

        uow.register(NotificationOp(DeleteDoiRequestSubmitNotificationBuilder.build(request=self.request)))


class DeleteDoiDeclineAction(OARepoDeclineAction):
    """Delete DOI decline action."""

    @override
    def apply(
        self,
        identity: Identity,
        state: RequestActionState,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Delete DOI."""
        self.request.topic.resolve()

        uow.register(NotificationOp(DeleteDoiRequestDeclineNotificationBuilder.build(request=self.request)))


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
    ) -> Any:
        """Decline doi request."""
        uow.register(NotificationOp(AssignDoiRequestDeclineNotificationBuilder.build(request=self.request)))
        return super().apply(identity, state, uow, *args, **kwargs)


class ValidateDataForDoiAction(OARepoSubmitAction, OarepoDoiActionMixin):
    """Validate record metadata."""

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
        """Validate record metadata."""
        topic = self.request.topic.resolve()
        errors = self.provider.mapping.metadata_check(topic)

        if len(errors) > 0:
            raise ValidationError(message=errors)
        uow.register(NotificationOp(AssignDoiRequestSubmitNotificationBuilder.build(request=self.request)))
