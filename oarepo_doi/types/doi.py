from invenio_requests.customizations import RequestType
from oarepo_runtime.i18n import lazy_gettext as _
from ..actions.doi import CreateDoiAction, ValidateDataForDoiAction
from oarepo_requests.types.ref_types import ModelRefTypes

class AssignDoiRequestType(RequestType):
    type_id = "assign_doi"
    name = _("assign_doi")

    available_actions = {
        **RequestType.available_actions,
        "accept": CreateDoiAction,
        "submit": ValidateDataForDoiAction,
    }

    receiver_can_be_none = True
    allowed_topic_ref_types = ModelRefTypes(published=True, draft=True)
