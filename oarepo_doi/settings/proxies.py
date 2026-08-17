# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Proxy objects for accessing the current application's doi settings service and resource."""

from __future__ import annotations

from flask import current_app
from werkzeug.local import LocalProxy

current_doi_settings = LocalProxy(lambda: current_app.extensions["doi-settings"])
