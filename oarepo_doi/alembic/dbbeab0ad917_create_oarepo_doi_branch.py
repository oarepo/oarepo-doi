#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create oarepo_doi branch."""

# revision identifiers, used by Alembic.
from __future__ import annotations

revision = "dbbeab0ad917"
down_revision = None
branch_labels = ("oarepo_doi",)
depends_on = "de9c14cbb0b2"


def upgrade() -> None:
    """Upgrade database."""


def downgrade() -> None:
    """Downgrade database."""
