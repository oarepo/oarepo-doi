import logging

from invenio_db import db

from invenio_records_resources.services import (
    RecordService,
    RecordServiceConfig,
    pagination_links,
)
from invenio_records_resources.services.base.config import (
    ConfiguratorMixin,
    FromConfig,
    SearchOptionsMixin,
)
from invenio_records_resources.services.errors import (
    PermissionDeniedError,
)
from invenio_records_resources.services.records.config import SearchOptions
from invenio_records_resources.services.records.params import (
    FacetsParam,
    PaginationParam,
    QueryStrParam,
    SortParam,
)

from invenio_users_resources.services.common import Link




from .models import CommunityDoiSettings, CommunityDoiSettingsAggregateModel
from . import facets
from .api import CommunityDoiSettingsAggregate
from .results import CommunityDoiSettingsItem, CommunityDoiSettingsList
from .schema import CommunityDoiSettingsSchema
from .permissions import DoiSettingsPermissionPolicy
log = logging.getLogger(__name__)
from .components import DoiSettingsComponent



class CommunityDoiSettingsSearchOptions(SearchOptions, SearchOptionsMixin):
    """Search options."""

    pagination_options = {
        "default_results_per_page": 25,
        "default_max_results": 10000,
    }


    params_interpreters_cls = [
        QueryStrParam,
        SortParam,
        PaginationParam,
        FacetsParam,
    ]

    facets = {
        "username": facets.username,
        "prefix": facets.prefix,
        "community_slug": facets.community_slug,
    }



class CommunityDoiSettingsLink(Link):
    """Short cut for writing record links."""

    @staticmethod
    def vars(record, vars):
        """Variables for the URI template."""
        # Some records don't have record.pid.pid_value yet (e.g. drafts)
        vars.update({"id": record.id})


class CommunityDoiSettingsServiceConfig(RecordServiceConfig, ConfiguratorMixin):
    """Requests service configuration."""

    # common configuration
    permission_policy_cls = DoiSettingsPermissionPolicy
    result_item_cls = CommunityDoiSettingsItem
    result_list_cls = CommunityDoiSettingsList

    search = CommunityDoiSettingsSearchOptions

    service_id = "community-doi"
    record_cls = CommunityDoiSettingsAggregate
    schema = FromConfig("DOI_SETTINGS_SERVICE_SCHEMA", CommunityDoiSettingsSchema)
    indexer_queue_name = "community-doi"
    index_dumper = None

    # links configuration
    links_item = {
        "self": Link("{+api}/doi_settings/{id}"),
    }
    links_search_item = {
      "self": Link("{+api}/doi_settings/{id}"),
    }
    links_search = pagination_links("{+api}/doi_settings{?args*}")

    components = [DoiSettingsComponent]


class CommunityDoiSettingsService(RecordService):
    """Users service."""

    @property
    def doi_settings_cls(self):
        """Alias for record_cls."""
        return self.record_cls

    def search(
        self,
        identity,
        params=None,
        search_preference=None,
        extra_filters=None,
        **kwargs,
    ):
        """Search for oai_runs."""
        self.require_permission(identity, "search")

        return super().search(
            identity,
            params=params,
            search_preference=search_preference,
            search_opts=self.config.search,
            permission_action="read",
            extra_filter=extra_filters,
            **kwargs,
        )

    def read(self, identity, id_):
        """Retrieve a oai_run."""
        # resolve and require permission
        doi_config = CommunityDoiSettingsAggregate.get_record(id_)
        if doi_config is None:
            raise PermissionDeniedError()

        self.require_permission(identity, "read", record=doi_config)

        # run components
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, doi_config=doi_config)

        return self.result_item(self, identity, doi_config, links_tpl=self.links_item_tpl)

    def rebuild_index(self, identity, uow=None):
        """Reindex all oai_runs managed by this service."""
        doi_settings = db.session.query(CommunityDoiSettings.id).yield_per(1000)
        self.indexer.bulk_index([u.id for u in doi_settings])
        return True
