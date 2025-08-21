#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Proxy objects for accessing the current application's doi settings service and resource."""

from __future__ import annotations

from flask import current_app
from werkzeug.local import LocalProxy

current_doi_settings = LocalProxy(lambda: current_app.extensions["doi-settings"])
