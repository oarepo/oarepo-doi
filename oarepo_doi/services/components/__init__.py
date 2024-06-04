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
        self.username = current_app.config.get("DATACITE_USERNAME")
        self.password = current_app.config.get("DATACITE_PASSWORD")
        self.url = current_app.config.get("DATACITE_URL")
        self.prefix = current_app.config.get("DATACITE_PREFIX")
        self.mapping = current_app.config.get("DATACITE_MAPPING")

    def create(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC_DRAFT":
            create_doi(self, record,data, None)

    def update_draft(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC_DRAFT":
            edit_doi(self, record)

    def update(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC_DRAFT" or self.mode == "AUTOMATIC":
            edit_doi(self, record)

    def publish(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC":
            create_doi(self, record, data, "publish")
        if self.mode == "AUTOMATIC_DRAFT":
            edit_doi(self, record, "publish")
