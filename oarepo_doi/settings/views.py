#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Blueprints for doi settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Blueprint, Flask


def create_api_blueprint(app: Flask) -> Blueprint:
    """Create DOI settings blueprint."""
    _ = app

    return app.extensions["doi-settings"].doi_settings_resource.as_blueprint()
