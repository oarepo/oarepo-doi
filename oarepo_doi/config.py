from oarepo_doi.notifications.builders.assign_doi import (
    AssignDoiRequestSubmitNotificationBuilder,
    AssignDoiRequestAcceptNotificationBuilder,
    AssignDoiRequestDeclineNotificationBuilder
)
from oarepo_doi.notifications.builders.delete_doi import (
    DeleteDoiRequestSubmitNotificationBuilder,
    DeleteDoiRequestAcceptNotificationBuilder,
    DeleteDoiRequestDeclineNotificationBuilder
)

NOTIFICATIONS_BUILDERS = {
    AssignDoiRequestSubmitNotificationBuilder.type: AssignDoiRequestSubmitNotificationBuilder,
    AssignDoiRequestAcceptNotificationBuilder.type: AssignDoiRequestAcceptNotificationBuilder,
    AssignDoiRequestDeclineNotificationBuilder.type: AssignDoiRequestDeclineNotificationBuilder,
    DeleteDoiRequestSubmitNotificationBuilder.type: DeleteDoiRequestSubmitNotificationBuilder,
    DeleteDoiRequestAcceptNotificationBuilder.type: DeleteDoiRequestAcceptNotificationBuilder,
    DeleteDoiRequestDeclineNotificationBuilder.type: DeleteDoiRequestDeclineNotificationBuilder,
}