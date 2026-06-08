#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI configuration."""

from __future__ import annotations

import idutils
from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.resources.serializers import (
    DataCite43JSONSerializer,  # pyright: ignore[reportAttributeAccessIssue]
)

from oarepo_doi.services.providers.client import DataCiteRecordAwareClient
from oarepo_doi.services.providers.provider import DataCiteRecordAwareProvider
from oarepo_doi.settings import facets

RDM_PERSISTENT_IDENTIFIER_PROVIDERS = [
    # DataCite DOI provider
    DataCiteRecordAwareProvider(
        "datacite",
        client=DataCiteRecordAwareClient("datacite", config_prefix="DATACITE"),
        label=_("DOI"),
    )
]

RDM_PERSISTENT_IDENTIFIERS = {
    "doi": {
        "providers": ["datacite"],
        "required": True,
        "label": _("DOI"),
        "validator": idutils.is_doi,  # pyright: ignore[reportAttributeAccessIssue]
        "normalizer": idutils.normalize_doi,  # pyright: ignore[reportAttributeAccessIssue]
        "is_enabled": DataCiteRecordAwareProvider.is_enabled,
        "ui": {"default_selected": "not_needed"},  # "yes", "no" or "not_needed"
    }
}

RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS = [
    # DataCite Concept DOI provider
    DataCiteRecordAwareProvider(
        "datacite",
        client=DataCiteRecordAwareClient("datacite", config_prefix="DATACITE"),
        serializer=DataCite43JSONSerializer(schema_context={"is_parent": True}),
        label=_("Concept DOI"),
    ),
]

RDM_PARENT_PERSISTENT_IDENTIFIERS = {
    "doi": {
        "providers": ["datacite"],
        "required": True,
        "condition": lambda rec: rec.pids.get("doi", {}).get("provider") == "datacite",
        "label": _("Concept DOI"),
        "validator": idutils.is_doi,  # pyright: ignore[reportAttributeAccessIssue]
        "normalizer": idutils.normalize_doi,  # pyright: ignore[reportAttributeAccessIssue]
        "is_enabled": DataCiteRecordAwareProvider.is_enabled,
    },
}

DOI_SETTINGS_SEARCH = {
    "facets": ["community_slug", "prefix"],
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
    },
}
DOI_SETTINGS_SORT_OPTIONS = {
    "newest": {
        "title": _("Newest"),
        "fields": ["-created"],
    },
}
