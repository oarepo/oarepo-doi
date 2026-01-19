#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Oarepo multiple model serializers."""

from __future__ import annotations

from typing import Any

from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import BaseSerializerSchema, JSONSerializer
from oarepo_runtime import current_runtime

"""
class DataCite43JSONSerializer(MarshmallowSerializer):

    def __init__(self, **options):
            super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=MultipleModelsSchema, <-- nase schema hier
            list_schema_cls=BaseListSchema,
            schema_kwargs={"dumpers": [JournalDataciteDumper()]},  # Order matters
            **options,
        )
"""


class OarepoDataciteJSONSerializer(MarshmallowSerializer):
    """Marshmallow based DataCite schema v4.3 serializer for records."""

    def __init__(self, **options: Any) -> None:
        """Construct."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=MultipleModelsSchema,
            list_schema_cls=BaseListSchema,
            schema_kwargs={"dumpers": []},  # Order matters
            **options,
        )


class MultipleModelsSchema(BaseSerializerSchema):
    """Multiple model repository serializer."""

    def dump(self, obj: Any, *, many: bool | None = None) -> Any:
        """Dump record data based on the model."""
        _ = many
        models = current_runtime.rdm_models_by_schema
        model = models[obj.schema]
        exports = model.exports
        datacite_serializer = None
        for e in exports:
            if e.code == "datacite":
                datacite_serializer = e.serializer

        if datacite_serializer is None:
            raise RuntimeError(f"No Datacite serializer defined for {obj.data['$schema']}")

        return datacite_serializer.dump_obj(obj)  # pyright: ignore[reportAttributeAccessIssue]
