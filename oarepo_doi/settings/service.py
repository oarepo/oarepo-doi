#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Service layer."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar, override

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
from invenio_records_resources.services.base.links import Link
from invenio_records_resources.services.errors import PermissionDeniedError
from invenio_records_resources.services.records.config import SearchOptions
from invenio_records_resources.services.records.params import (
    FacetsParam,
    PaginationParam,
    QueryStrParam,
    SortParam,
)

from . import facets
from .api import CommunityDoiSettingsAggregate
from .components import DoiSettingsComponent
from .models import CommunityDoiSettings
from .permissions import DoiSettingsPermissionPolicy
from .results import CommunityDoiSettingsItem, CommunityDoiSettingsList
from .schema import CommunityDoiSettingsSchema

if TYPE_CHECKING:
    from collections.abc import Mapping

    from flask_principal import Identity
    from invenio_records.api import RecordBase
    from invenio_records_resources.services.uow import UnitOfWork
    from invenio_requests.services.requests.results import RequestItem
log = logging.getLogger(__name__)


class CommunityDoiSettingsSearchOptions(SearchOptions, SearchOptionsMixin):
    """Search options."""

    pagination_options: ClassVar[dict[str, int]] = {
        "default_results_per_page": 25,
        "default_max_results": 10000,
    }

    params_interpreters_cls: ClassVar[list[type]] = [
        QueryStrParam,
        SortParam,
        PaginationParam,
        FacetsParam,
    ]

    facets: ClassVar[dict[str, Any]] = {
        "username": facets.username,
        "prefix": facets.prefix,
        "community_slug": facets.community_slug,
    }


class CommunityDoiSettingsLink(Link):
    """Shortcut for writing record links."""

    @staticmethod
    @override
    def vars(obj: RecordBase, vars: dict) -> None:
        """Variables for the URI template."""
        # Some records don't have record.pid.pid_value yet (e.g. drafts)
        vars.update({"id": obj.id})


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
    links_item: ClassVar[dict[str, Link]] = {
        "self": Link("{+api}/doi_settings/{id}"),
    }

    links_search_item: ClassVar[dict[str, Link]] = {
        "self": Link("{+api}/doi_settings/{id}"),
    }

    links_search: ClassVar[Mapping[str, Link]] = pagination_links("{+api}/doi_settings{?args*}")

    components: ClassVar[list[type[DoiSettingsComponent]]] = [DoiSettingsComponent]


class CommunityDoiSettingsService(RecordService):
    """Users service."""

    @property
    def doi_settings_cls(self) -> RecordBase:
        """Alias for record_cls."""
        return self.record_cls

    def search(
        self,
        identity: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        search_preference: Any | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RequestItem:
        """Search for oai_runs."""
        self.require_permission(identity, "search")

        return super().search(
            identity,
            params=params,
            search_preference=search_preference,
            search_opts=self.config.search,
            permission_action="read",
            expand=expand,
            **kwargs,
        )

    def read(
        self, identity: Identity, id_: str, expand: bool = False, action: str = "read", **kwargs: Any
    ) -> RequestItem:
        """Retrieve a oai_run."""
        # resolve and require permission
        _, _, _ = action, expand, kwargs
        doi_config = CommunityDoiSettingsAggregate.get_record(id_)
        if doi_config is None:
            raise PermissionDeniedError

        self.require_permission(identity, "read", record=doi_config)

        # run components
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, doi_config=doi_config)

        return self.result_item(self, identity, doi_config, links_tpl=self.links_item_tpl)

    def rebuild_index(self, identity: Identity, uow: UnitOfWork | None = None) -> Any:
        """Reindex all oai_runs managed by this service."""
        _, _ = identity, uow
        doi_settings = db.session.query(CommunityDoiSettings.id).yield_per(1000)
        self.indexer.bulk_index([u.id for u in doi_settings])
        return True
