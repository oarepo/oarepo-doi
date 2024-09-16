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
        if not community:
            credentials = current_app.config.get(
                "DATACITE_CREDENTIALS_DEFAULT"
            )
        else:
            credentials_def = current_app.config.get("DATACITE_CREDENTIALS")

            credentials =  credentials_def.get(community, None)

        self.username = credentials["username"]
        self.password = credentials["password"]
        self.prefix = credentials["prefix"]

    def create(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC_DRAFT":
            slug = community_slug_for_credentials(
                record.parent["communities"].get("default", None)
            )
            self.credentials(slug)
            create_doi(self, record, data, None)

    def update_draft(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC_DRAFT" or self.mode == "ON_EVENT":
            slug = community_slug_for_credentials(
                record.parent["communities"].get("default", None)
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
                record.parent["communities"].get("default", None)
            )
            self.credentials(slug)
            edit_doi(self, record)

    def publish(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC":
            slug = community_slug_for_credentials(
                record.parent["communities"].get("default", None)
            )
            self.credentials(slug)
            create_doi(self, record, data, "publish")
        if self.mode == "AUTOMATIC_DRAFT":
            slug = community_slug_for_credentials(
                record.parent["communities"].get("default", None)
            )
            self.credentials(slug)
            edit_doi(self, record, "publish")
