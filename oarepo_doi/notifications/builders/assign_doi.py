from oarepo_requests.notifications.builders.oarepo import (
    OARepoRequestActionNotificationBuilder,
)
from oarepo_requests.notifications.generators import EntityRecipient


class AssignDoiRequestSubmitNotificationBuilder(OARepoRequestActionNotificationBuilder):
    type = "assign-doi-request-event.submit"

    recipients = [EntityRecipient(key="request.receiver")]  # email only


class AssignDoiRequestAcceptNotificationBuilder(OARepoRequestActionNotificationBuilder):
    type = "assign-doi-request-event.accept"

    recipients = [EntityRecipient(key="request.created_by")]


class AssignDoiRequestDeclineNotificationBuilder(
    OARepoRequestActionNotificationBuilder
):
    type = "assign-doi-request-event.decline"

    recipients = [EntityRecipient(key="request.created_by")]
