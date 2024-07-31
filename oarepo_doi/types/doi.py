from invenio_requests.customizations import RequestType
from oarepo_runtime.i18n import lazy_gettext as _
from ..actions.doi import CreateDoiAction, EditDoiAction
from oarepo_requests.types.ref_types import ModelRefTypes

class CreateDoiRequestType(RequestType):
    type_id = "create_doi"
    name = _("create_doi")

    available_actions = {
        **RequestType.available_actions,
        "accept": CreateDoiAction,
    }

    receiver_can_be_none = True
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)

class EditDoiRequestType(RequestType):
    type_id = "edit_doi"
    name = _("edit_doi")

    available_actions = {
        **RequestType.available_actions,
        "accept": EditDoiAction,
    }

    receiver_can_be_none = True
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)