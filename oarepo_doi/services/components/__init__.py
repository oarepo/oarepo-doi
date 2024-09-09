from flask import current_app
from invenio_records_resources.services.records.components import ServiceComponent

from oarepo_doi.api import community_slug_for_credentials, create_doi, edit_doi


class DoiComponent(ServiceComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mode = current_app.config.get("DATACITE_MODE")
        self.url = current_app.config.get("DATACITE_URL")
        self.mapping = current_app.config.get("DATACITE_MAPPING")
        self.specified_doi = current_app.config.get("DATACITE_SPECIFIED_ID")

        self.username = None
        self.password = None
        self.prefix = None

    def credentials(self, community):
        credentials_def = current_app.config.get("DATACITE_CREDENTIALS")

        community_credentials = getattr(credentials_def, community, None)
        if (
            community_credentials is None
            and "DATACITE_CREDENTIALS_DEFAULT" in current_app.config
        ):
            community_credentials = current_app.config.get(
                "DATACITE_CREDENTIALS_DEFAULT"
            )
        self.username = community_credentials["username"]
        self.password = community_credentials["password"]
        self.prefix = community_credentials["prefix"]

    def create(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC_DRAFT":
            slug = community_slug_for_credentials(
                record.parent["communities"]["default"]
            )
            self.credentials(slug)
            create_doi(self, record, data, None)

    def update_draft(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC_DRAFT" or self.mode == "ON_EVENT":
            slug = community_slug_for_credentials(
                record.parent["communities"]["default"]
            )

            self.credentials(slug)
            edit_doi(self, record)

    def update(self, identity, data=None, record=None, **kwargs):
        if (
            self.mode == "AUTOMATIC_DRAFT"
            or self.mode == "AUTOMATIC"
            or self.mode == "ON_EVENT"
        ):
            slug = community_slug_for_credentials(
                record.parent["communities"]["default"]
            )
            self.credentials(slug)
            edit_doi(self, record)

    def publish(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC":
            slug = community_slug_for_credentials(
                record.parent["communities"]["default"]
            )
            self.credentials(slug)
            create_doi(self, record, data, "publish")
        if self.mode == "AUTOMATIC_DRAFT":
            slug = community_slug_for_credentials(
                record.parent["communities"]["default"]
            )
            self.credentials(slug)
            edit_doi(self, record, "publish")
