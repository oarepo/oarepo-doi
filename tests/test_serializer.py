#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for resource serializers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from oarepo_doi.resources import serializers
from oarepo_doi.resources.serializers import MultipleModelsSchema


class DummyDataciteSerializer:
    """Datacite serializer test double."""

    def dump_obj(self, obj):
        """Return serialized record data."""
        return {"serialized": obj.schema}


def test_multiple_models_schema(monkeypatch):

    record = SimpleNamespace(schema="test-schema", data={"$schema": "test-schema"})
    model = SimpleNamespace(
        exports=[
            SimpleNamespace(code="json", serializer=object()),
            SimpleNamespace(code="datacite", serializer=DummyDataciteSerializer()),
        ],
    )
    monkeypatch.setattr(
        serializers,
        "current_runtime",
        SimpleNamespace(rdm_models_by_schema={"test-schema": model}),
    )

    assert MultipleModelsSchema().dump(record) == {"serialized": "test-schema"}


def test_multiple_models_schema_no_datacite_export(monkeypatch):
    record = SimpleNamespace(schema="test-schema", data={"$schema": "test-schema"})
    model = SimpleNamespace(exports=[SimpleNamespace(code="json", serializer=object())])
    monkeypatch.setattr(
        serializers,
        "current_runtime",
        SimpleNamespace(rdm_models_by_schema={"test-schema": model}),
    )

    with pytest.raises(RuntimeError, match="No Datacite serializer defined for test-schema"):
        MultipleModelsSchema().dump(record)



