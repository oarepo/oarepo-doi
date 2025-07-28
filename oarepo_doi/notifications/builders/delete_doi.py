from oarepo_requests.notifications.builders.oarepo import (
    OARepoRequestActionNotificationBuilder,
)
from oarepo_requests.notifications.generators import EntityRecipient


class DeleteDoiRequestSubmitNotificationBuilder(OARepoRequestActionNotificationBuilder):
    type = "delete-doi-request-event.submit"

    recipients = [EntityRecipient(key="request.receiver")]


class DeleteDoiRequestAcceptNotificationBuilder(OARepoRequestActionNotificationBuilder):
    type = "delete-doi-request-event.accept"

    recipients = [EntityRecipient(key="request.created_by")]


class DeleteDoiRequestDeclineNotificationBuilder(
    OARepoRequestActionNotificationBuilder
):
    type = "delete-doi-request-event.decline"

    recipients = [EntityRecipient(key="request.created_by")]
