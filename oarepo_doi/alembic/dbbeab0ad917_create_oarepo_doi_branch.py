#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create oarepo_doi branch."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dbbeab0ad917'
down_revision = None
branch_labels = ('oarepo_doi',)
depends_on = 'de9c14cbb0b2'


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
