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

from typing import Any

from invenio_administration.generators import Administration
from invenio_records_permissions import BasePermissionPolicy
from invenio_records_permissions.generators import SystemProcess


class DoiSettingsPermissionPolicy(BasePermissionPolicy):
    """Permission policy for DOI settings."""

    can_create: Any = [SystemProcess(), Administration()]  # noqa: RUF012
    can_read: Any = [SystemProcess(), Administration()]  # noqa: RUF012
    can_search: Any = [SystemProcess(), Administration()]  # noqa: RUF012
    can_update: Any = [SystemProcess(), Administration()]  # noqa: RUF012
    can_delete: Any = [SystemProcess(), Administration()]  # noqa: RUF012
