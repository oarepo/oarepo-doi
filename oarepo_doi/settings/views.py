# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Blueprints for doi settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Blueprint, Flask


def create_api_blueprint(app: Flask) -> Blueprint:
    """Create DOI settings blueprint."""
    _ = app

    return app.extensions["doi-settings"].doi_settings_resource.as_blueprint()
