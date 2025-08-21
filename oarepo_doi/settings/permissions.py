#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI settings permission policy."""

from __future__ import annotations

from typing import ClassVar

from invenio_administration.generators import Administration
from invenio_records_permissions import BasePermissionPolicy
from invenio_records_permissions.generators import SystemProcess


class DoiSettingsPermissionPolicy(BasePermissionPolicy):
    """Permission policy for DOI settings."""

    can_create: ClassVar[list] = [SystemProcess(), Administration()]
    can_read: ClassVar[list] = [SystemProcess(), Administration()]
    can_search: ClassVar[list] = [SystemProcess(), Administration()]
    can_update: ClassVar[list] = [SystemProcess(), Administration()]
    can_delete: ClassVar[list] = [SystemProcess(), Administration()]
