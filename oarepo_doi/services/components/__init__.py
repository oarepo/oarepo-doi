import json
import requests
from invenio_records_resources.services.records.components import ServiceComponent
from flask import current_app
from invenio_base.utils import obj_or_import_string

from oarepo_doi.api import create_doi, edit_doi


class DoiComponent(ServiceComponent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mode = current_app.config.get("DATACITE_MODE")
        self.url = current_app.config.get("DATACITE_URL")
        self.mapping = current_app.config.get("DATACITE_MAPPING")

        self.username = None
        self.password = None
        self.prefix = None



    def credentials(self, community):
        credentials_def = current_app.config.get("DATACITE_CREDENTIALS")

        community_credentials = getattr(credentials_def, community, None)
        if community_credentials is None and "DATACITE_CREDENTIALS_DEFAULT" in current_app.config:
            community_credentials = current_app.config.get("DATACITE_CREDENTIALS_DEFAULT")
        self.username = community_credentials["username"]
        self.password = community_credentials["password"]
        self.prefix = community_credentials["prefix"]

    def create(self, identity, data=None, record=None, **kwargs):

        if self.mode == "AUTOMATIC_DRAFT":
            self.credentials(data['parent']['communities']['default'])
            create_doi(self, record,data, None)

    def update_draft(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC_DRAFT":
            self.credentials(data['parent']['communities']['default'])
            edit_doi(self, record)

    def update(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC_DRAFT" or self.mode == "AUTOMATIC":
            self.credentials(data['parent']['communities']['default'])
            edit_doi(self, record)

    def publish(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC":
            self.credentials(data['parent']['communities']['default'])
            create_doi(self, record, data, "publish")
        if self.mode == "AUTOMATIC_DRAFT":
            self.credentials(data['parent']['communities']['default'])
            edit_doi(self, record, "publish")
