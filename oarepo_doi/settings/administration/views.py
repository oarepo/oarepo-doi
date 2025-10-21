#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI settings administration views."""

from __future__ import annotations

from typing import Any, ClassVar

from invenio_administration.views.base import (
    AdminFormView,
    AdminResourceDetailView,
    AdminResourceListView,
)
from invenio_i18n import lazy_gettext as _


class DOIFormMixin:
    """DOI settings mixin class."""

    form_fields: ClassVar[dict[str, dict[str, Any]]] = {
        "username": {
            "order": 1,
            "text": _("Datacite ID"),
        },
        "password": {
            "order": 2,
            "text": _("Password"),
        },
        "prefix": {
            "order": 3,
            "text": _("Prefix"),
        },
        "community_slug": {
            "order": 4,
            "text": _("Community slug"),
        },
    }


class DOIListView(AdminResourceListView):
    """DOI settings list view."""

    api_endpoint = "/doi_settings"
    extension_name = "doi-settings"
    name = "oarepo_doi"
    url = "oarepo/doi"

    resource_config = "doi_settings_resource"

    title = _("DOI Configuration")
    category = "Site management"
    pid_path = "id"
    icon = "world"
    order = 1
    menu_label = _("DOI Configuration")

    display_search = True
    display_delete = True
    display_edit = True
    display_create = True

    item_field_list: ClassVar[dict[str, dict[str, Any]]] = {
        "community_slug": {"text": _("Community"), "order": 1, "width": 4},
        "prefix": {"text": _("Prefix"), "order": 2, "width": 4},
        "username": {"text": _("Datacite ID"), "order": 3, "width": 4},
        "created": {"text": _("Created"), "order": 4, "width": 4},
    }

    search_config_name = "DOI_SETTINGS_SEARCH"
    search_facets_config_name = "DOI_SETTINGS_FACETS"
    search_sort_config_name = "DOI_SETTINGS_SORT_OPTIONS"

    create_view_name = "oarepo_doi_create"


class DOICreateView(DOIFormMixin, AdminFormView):
    """DOI settings create view."""

    name = "oarepo_doi_create"
    url = "oarepo/doi/create"
    resource_config = "doi_settings_resource"
    pid_path = "id"
    api_endpoint = "/doi_settings"
    title = _("Create DOI configuration")
    extension_name = "doi-settings"
    list_view_name = "oarepo_doi"
    template = "invenio_administration/create.html"


class DOIEditView(DOIFormMixin, AdminFormView):
    """DOI settings edit view."""

    name = "oarepo_doi_edit"
    url = "oarepo/doi/<pid_value>/edit"
    resource_config = "doi_settings_resource"
    pid_path = "id"
    api_endpoint = "/doi_settings"
    title = _("Edit DOI configuration")
    extension_name = "doi-settings"
    template = "invenio_administration/edit.html"
    list_view_name = "oarepo_doi"


class DOIDetailView(AdminResourceDetailView):
    """DOI settings detail view."""

    url = "oarepo/doi/<pid_value>"
    api_endpoint = "/doi_settings"
    name = "oarepo_doi_detail"
    resource_config = "doi_settings_resource"
    title = _("DOI configuration detail")
    extension_name = "doi-settings"

    display_delete = True
    display_edit = True

    list_view_name = "oarepo_doi"
    pid_path = "id"

    item_field_list: ClassVar[dict[str, dict[str, Any]]] = {
        "community_slug": {"text": _("Community"), "order": 1, "width": 4},
        "prefix": {"text": _("Prefix"), "order": 2, "width": 4},
        "username": {"text": _("Datacite ID"), "order": 3, "width": 4},
        "created": {"text": _("Created"), "order": 4, "width": 4},
        "updated": {"text": _("Updated"), "order": 5, "width": 4},
    }
