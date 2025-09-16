#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""DOI oarepo provider."""

from __future__ import annotations

import uuid

import requests  # type: ignore[import-untyped]

from invenio_access.permissions import system_identity
from invenio_communities import current_communities

from invenio_search.engine import dsl



def community_slug_for_credentials(value):
    if not value:
        return None
    try:
        uuid.UUID(value, version=4)
        search = current_communities.service._search(
            "search",
            system_identity,
            {},
            None,
            extra_filter=dsl.Q("term", **{"id": value}),
        )
        community = search.execute()
        c = list(community.hits.hits)[0]
        return c._source.slug
    except:
        return value