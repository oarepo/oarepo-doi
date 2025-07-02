from .config import NOTIFICATIONS_BUILDERS, DOI_SETTINGS_SEARCH, DOI_SETTINGS_FACETS, DOI_SETTINGS_SORT_OPTIONS
from deepmerge import conservative_merger
from invenio_base.utils import obj_or_import_string
from functools import cached_property

class OARepoDOI(object):
    """OARepo DOI extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.app = app
        app.extensions["doi-settings"] = self
        self.init_config(app)



    def init_config(self, app):
        """Initialize configuration."""
        if "DATACITE_URL" not in app.config:
            app.config["DATACITE_URL"] = "https://api.datacite.org/dois"
        if "DATACITE_MODE" not in app.config:
            app.config["DATACITE_MODE"] = "ON_EVENT"
        if "DATACITE_SPECIFIED_ID" not in app.config:
            app.config["DATACITE_SPECIFIED_ID"] = False

        app_notification_builders = app.config.setdefault(
            "NOTIFICATIONS_BUILDERS", {}
        )
        app.config["NOTIFICATIONS_BUILDERS"] = conservative_merger.merge(
            app_notification_builders, NOTIFICATIONS_BUILDERS
        )
        app.config.setdefault("DOI_SETTINGS_SEARCH", DOI_SETTINGS_SEARCH)
        app.config.setdefault("DOI_SETTINGS_FACETS", DOI_SETTINGS_FACETS)
        app.config.setdefault("DOI_SETTINGS_SORT_OPTIONS", DOI_SETTINGS_SORT_OPTIONS)

    @cached_property
    def doi_settings_service(self):
        """Get the OAI run service."""
        return obj_or_import_string(
            self.app.config.get(
                    "DOI_CONFIG_SERVICE",
                    "oarepo_doi.settings.service:CommunityDoiSettingsService",
            ),
        )(self.doi_settings_service_config)

    @cached_property
    def doi_settings_service_config(self):
        """Get the OAI run service config."""
        return obj_or_import_string(
            self.app.config.get(
                    "DOI_CONFIG_SERVICE_CONFIG",
                    "oarepo_doi.settings.service:CommunityDoiSettingsServiceConfig",
            ),
        ).build(self.app)

    @cached_property
    def doi_settings_resource_config(self):
        """Get the OAI run resource config."""
        return obj_or_import_string(
            self.app.config.get(
                "DOI_CONFIG_RESOURCE_CONFIG",
                "oarepo_doi.settings.resource:CommunityDoiSettingsResourceConfig",
            ),
        )()

    @cached_property
    def doi_settings_resource(self):
        """Get the OAI run resource."""
        return obj_or_import_string(
            self.app.config.get(
                    "DOI_CONFIG_RESOURCE",
                    "oarepo_doi.settings.resource:CommunityDoiSettingsResource",
                ),
        )(self.doi_settings_resource_config, self.doi_settings_service)

def api_finalize_app(app):
    """Finalize app."""
    finalize_app(app)


def finalize_app(app):
    """Finalize app."""
    init(app)
def init(app):
    """Init app."""
    ext = app.extensions["doi-settings"]
    sregistry = app.extensions["invenio-records-resources"].registry
    sregistry.register(
        ext.doi_settings_service, service_id=ext.doi_settings_service_config.service_id
    )
    # Register indexers
    iregistry = app.extensions["invenio-indexer"].registry
    iregistry.register(
        ext.doi_settings_service.indexer,
        indexer_id=ext.doi_settings_service_config.service_id,
    )



