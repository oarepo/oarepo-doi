from flask import current_app
from invenio_records_resources.services.records.components import ServiceComponent
import importlib_metadata
from flask import current_app


class DoiComponent(ServiceComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mode = current_app.config.get("DATACITE_MODE")

    def provider(self, topic):

        for x in importlib_metadata.entry_points(
                group='invenio_base.apps'
        ):
            if x.name == "oarepo_rdm":
                rdm = x.load()
                break
        service_id = rdm(app=current_app).record_service_from_pid_type(topic.pid.pid_type, topic.is_draft).id
        providers = current_app.config.get("RDM_PERSISTENT_IDENTIFIER_PROVIDERS")

        for _provider in providers:
            if _provider.name == "datacite":
                provider = _provider
                break
        provider.service_id = service_id
        return provider

    def create(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC_DRAFT":
            self.provider(record).create_and_reserve(record)

    def update_draft(self, identity, data=None, record=None, **kwargs):
        if self.mode == "AUTOMATIC_DRAFT" or self.mode == "ON_EVENT_DRAFT":
            self.provider(record).update(record)

    def update(self, identity, data=None, record=None, **kwargs):
        self.provider(record).update(record)

    def publish(self, identity, data=None, record=None, draft=None, **kwargs):
        if record.pids is None:
            record.pids = {}
        if self.mode == "AUTOMATIC":
            self.provider(record).create_and_reserve(record,  event = "publish")
        if self.mode == "AUTOMATIC_DRAFT" or self.mode == "ON_EVENT_DRAFT":
            self.provider(record).update(record, event ="publish")

    def new_version(self, identity, draft=None, record=None, **kwargs):
        """Update draft metadata."""
        doi_value = self.provider.get_doi_value(record)
        if doi_value is not None:
            self.provider.remove_doi_value(draft)


    def delete_draft(self, identity, draft=None, record=None, force=False):
        doi_value = self.provider.get_doi_value(record)
        pid_doi = self.provider.get_pid_doi_value(record)
        if hasattr(pid_doi, "status") and pid_doi.status.value == "K":
            if doi_value is not None:
                self.provider.delete(draft)