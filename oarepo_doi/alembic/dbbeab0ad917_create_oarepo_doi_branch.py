# SPDX-FileCopyrightText: 2016-2018 CERN
# SPDX-License-Identifier: MIT

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
