#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for DOI settings models."""

from __future__ import annotations

from types import SimpleNamespace

from oarepo_doi.settings.models import CommunityDoiSettingsAggregateModel


def test_aggregate_model_obj_returns_existing_model_obj():
    """Aggregate model returns existing model object."""
    model_obj = SimpleNamespace(id="settings-id")
    aggregate_model = CommunityDoiSettingsAggregateModel(model_obj=model_obj)

    assert aggregate_model.model_obj is model_obj


def test_aggregate_model_version_id():
    """Aggregate model version is static."""
    assert CommunityDoiSettingsAggregateModel().version_id == 1
