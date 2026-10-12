# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT
"""Utilities for DOI settings."""

from __future__ import annotations

from invenio_db.utils import rebuild_encrypted_properties

from .models import CommunityDoiSettings


def rebuild_doi_settings_passwords(old_key: str) -> None:
    """Re-encrypt community DataCite passwords after secret-key rotation."""
    rebuild_encrypted_properties(old_key, CommunityDoiSettings, ["password"])
