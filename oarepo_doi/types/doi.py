from invenio_requests.customizations import RequestType

from oarepo_doi.actions.doi import DoiDraftAction


class DoiRequestType(RequestType):
    available_actions = {
        **RequestType.available_actions,
        "create_draft": DoiDraftAction,
        "publish_draft": DoiPublishAction,
    }

    receiver_can_be_none = True