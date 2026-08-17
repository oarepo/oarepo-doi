# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""DOI settings facets."""

from __future__ import annotations

from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.facets.facets import TermsFacet

community_slug = TermsFacet(field="community_slug", label=_("Community slug"))  # pyright: ignore[reportArgumentType]
username = TermsFacet(field="username", label=_("Username"))  # pyright: ignore[reportArgumentType]
prefix = TermsFacet(field="prefix", label=_("Prefix"))  # pyright: ignore[reportArgumentType]
