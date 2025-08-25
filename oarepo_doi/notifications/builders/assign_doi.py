#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Assign DOI notification builder."""

from __future__ import annotations

from typing import ClassVar

from oarepo_requests.notifications.builders.oarepo import (
    OARepoRequestActionNotificationBuilder,
)
from oarepo_requests.notifications.generators import EntityRecipient


class AssignDoiRequestSubmitNotificationBuilder(OARepoRequestActionNotificationBuilder):
    """Submit DOI notification builder."""

    type = "assign-doi-request-event.submit"

    recipients: ClassVar[list[EntityRecipient]] = [EntityRecipient(key="request.receiver")]  # email only


class AssignDoiRequestAcceptNotificationBuilder(OARepoRequestActionNotificationBuilder):
    """Accept DOI notification builder."""

    type = "assign-doi-request-event.accept"

    recipients: ClassVar[list[EntityRecipient]] = [EntityRecipient(key="request.created_by")]


class AssignDoiRequestDeclineNotificationBuilder(OARepoRequestActionNotificationBuilder):
    """Decline DOI notification builder."""

    type = "assign-doi-request-event.decline"

    recipients: ClassVar[list[EntityRecipient]] = [EntityRecipient(key="request.created_by")]
