from invenio_administration.generators import Administration
from invenio_records_permissions import BasePermissionPolicy
from invenio_records_permissions.generators import SystemProcess


class DoiSettingsPermissionPolicy(BasePermissionPolicy):
    """Permission policy for DOI settings."""

    can_create = [SystemProcess(), Administration()]
    can_read = [SystemProcess(), Administration()]
    can_search = [SystemProcess(), Administration()]
    can_update = [SystemProcess(), Administration()]
    can_delete = [SystemProcess(), Administration()]
