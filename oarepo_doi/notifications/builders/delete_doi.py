#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Delete DOI notification builder."""

from __future__ import annotations

from typing import ClassVar

from oarepo_requests.notifications.builders.oarepo import (
    OARepoRequestActionNotificationBuilder,
)
from oarepo_requests.notifications.generators import EntityRecipient


class DeleteDoiRequestSubmitNotificationBuilder(OARepoRequestActionNotificationBuilder):
    """Submit DOI deletion notification builder."""

    type = "delete-doi-request-event.submit"

    recipients: ClassVar[list[EntityRecipient]] = [EntityRecipient(key="request.receiver")]


class DeleteDoiRequestAcceptNotificationBuilder(OARepoRequestActionNotificationBuilder):
    """Accept DOI deletion notification builder."""

    type = "delete-doi-request-event.accept"

    recipients: ClassVar[list[EntityRecipient]] = [EntityRecipient(key="request.created_by")]


class DeleteDoiRequestDeclineNotificationBuilder(OARepoRequestActionNotificationBuilder):
    """Decline DOI deletion notification builder."""

    type = "delete-doi-request-event.decline"

    recipients: ClassVar[list[EntityRecipient]] = [EntityRecipient(key="request.created_by")]
