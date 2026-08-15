#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for DOI settings administration views."""

from __future__ import annotations

import pytest

from oarepo_doi.settings.administration.views import (
    DOIDetailView,
    DOIFormMixin,
    DOIListView,
)


def test_doi_form_fields_are_present():
    """DOI form contains expected fields."""
    assert set(DOIFormMixin.form_fields) == {"username", "password", "prefix", "community_slug"}


@pytest.mark.parametrize("view_cls", [DOIListView, DOIDetailView])
def test_doi_administration_display_fields_are_present(view_cls):
    """Display views contain expected DOI settings fields."""
    assert "community_slug" in view_cls.item_field_list
    assert "prefix" in view_cls.item_field_list
    assert "username" in view_cls.item_field_list
    assert "created" in view_cls.item_field_list
