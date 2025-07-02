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
from invenio_i18n import lazy_gettext as _
from oarepo_doi.settings import facets

NOTIFICATIONS_BUILDERS = {
    AssignDoiRequestSubmitNotificationBuilder.type: AssignDoiRequestSubmitNotificationBuilder,
    AssignDoiRequestAcceptNotificationBuilder.type: AssignDoiRequestAcceptNotificationBuilder,
    AssignDoiRequestDeclineNotificationBuilder.type: AssignDoiRequestDeclineNotificationBuilder,
    DeleteDoiRequestSubmitNotificationBuilder.type: DeleteDoiRequestSubmitNotificationBuilder,
    DeleteDoiRequestAcceptNotificationBuilder.type: DeleteDoiRequestAcceptNotificationBuilder,
    DeleteDoiRequestDeclineNotificationBuilder.type: DeleteDoiRequestDeclineNotificationBuilder,
}


DOI_SETTINGS_SEARCH = {
    "facets": [
        "community_slug",
        "prefix"
    ],
    "sort": ["newest"],
    "sort_default": "newest",
    "sort_default_no_query": "newest",
}

DOI_SETTINGS_FACETS = {
    "community_slug": {
        "facet": facets.community_slug,
        "ui": {
            "field": "community_slug",
        },
    },
    "prefix": {
        "facet": facets.prefix,
        "ui": {
            "field": "prefix",
        },
    }
}
DOI_SETTINGS_SORT_OPTIONS = {
    "newest": dict(
        title=_("Newest"),
        fields=["-created"],
    ),
}