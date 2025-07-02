from datetime import datetime
from uuid import UUID

from invenio_db import db
from invenio_records.dumpers import SearchDumper
from invenio_records.dumpers.indexedat import IndexedAtDumperExt
from invenio_records.systemfields import ModelField
from invenio_records_resources.records.systemfields import IndexField
from invenio_users_resources.records.api import BaseAggregate, AggregatePID

from .models import CommunityDoiSettings, CommunityDoiSettingsAggregateModel


class CommunityDoiSettingsAggregate(BaseAggregate):
    """An aggregate of information about a community doi settings."""

    model_cls = CommunityDoiSettingsAggregateModel
    """The model class for the request."""

    dumper = SearchDumper(
        extensions=[IndexedAtDumperExt()],
        model_fields={
            "id": ("uuid", UUID),
        },
    )

    prefix = ModelField("prefix", dump_type=str)

    username = ModelField("username", dump_type=str)

    id = ModelField("id", dump_type=UUID)

    password = ModelField("password", dump=False)

    community_slug =  ModelField("community_slug", dump_type=str)

    index = IndexField(
        "doi-settings-doi-settings-v1.0.0", search_alias="doi-settings"
    )

    """Needed to emulate pid access."""
    pid = AggregatePID("id")



    @classmethod
    def create(cls, data, id_=None, **kwargs):
        """Create a domain."""

        return CommunityDoiSettingsAggregate(data,
                                             model=CommunityDoiSettingsAggregateModel(model_obj=CommunityDoiSettings()))


    @classmethod
    def get_record(cls, id_):
        """Get the user via the specified ID."""
        with db.session.no_autoflush:
            settings = CommunityDoiSettings.query.get(id_)
            settings.password = ""

            return cls.from_model(settings)

    def delete(self, force=True):
        """Delete the domain."""
        db.session.delete(self.model.model_obj)

