#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI settings facets."""

from __future__ import annotations

from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.facets.facets import TermsFacet

community_slug = TermsFacet(field="community_slug", label=_("Community slug"))
username = TermsFacet(field="username", label=_("Username"))
prefix = TermsFacet(field="prefix", label=_("Prefix"))
