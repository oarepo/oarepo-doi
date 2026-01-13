from flask_resources.serializers import BaseSerializerSchema
# from oarepo_runtime import current_runtime

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


class MultipleModelsSchema(BaseSerializerSchema):
    def dump(self, obj, *, many: bool | None = None):
        models = current_runtime.rdm_models_by_schema
        model = models[obj.schema]
        exports = model.exports
        datacite_serializer = None
        for e in exports:
            if e.code == "datacite":
                datacite_serializer = e.serializer

        if datacite_serializer is None:
            raise RuntimeError(
                f"No Datacite serializer defined for {obj.data['$schema']}"
            )

        return datacite_serializer.dump_obj(obj)
