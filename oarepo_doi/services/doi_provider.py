from invenio_base.utils import obj_or_import_string
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from invenio_access.permissions import system_identity
from invenio_pidstore.models import PersistentIdentifier
from marshmallow import ValidationError
from flask import current_app
from invenio_pidstore.providers.base import BaseProvider
from invenio_db import db
from .relations import get_latest, get_doi_versions
from oarepo_doi.services.doi_client import DOIClient

class DOIProvider:

    prefix = ""

    @property
    def mapping(self):
        """Return DOI mode."""
        return obj_or_import_string(current_app.config.get("DATACITE_MAPPING"))()

    def generate_doi(self, record):
        print(record.id)
        return f"{self.prefix}/{record['id']}"

    def get_doi_value(self, record):
        pids = record.get("pids", {})
        return pids.get("doi", {}).get("identifier")

    def remove_doi_value(self, record):
        pids = record.get("pids", {})
        if "doi" in pids:
            pids.pop("doi")
        record.commit()

    def create_pid(self, record, doi_value):
        if not hasattr(record, "parent"):
            pid_status = "R"
        else:
            pid_status = "N" if record.is_draft else "R"
        try:
            BaseProvider.create("doi", doi_value, "rec", record.id, pid_status)
            db.session.commit()
        except:
            pass

    def add_doi_value(self, record, doi):
        pids = record.get("pids", {})
        pids["doi"] = {"provider": "datacite", "identifier": doi}

        record.pids = pids
        record.commit()

    def get_pid_doi_value(self, record):
        try:
            return PersistentIdentifier.get_by_object("doi", "rec", record.id)
        except:
            return None

    def initialize_client(self, record):
        client = DOIClient()
        _, _, prefix = client.credentials(record)
        self.prefix = prefix
        return client
    def add_links(self, record):
        if type(record) is dict and "links" in record:
            return record
        record_service = get_record_service_for_record(record)
        if record_service is not None and hasattr(record_service, "links_item_tpl"):
            record["links"] = record_service.links_item_tpl.expand(system_identity, record) #error pokud nie
        return record

    def create(self, record, make_findable = False):
        """Create new draft, create new findable."""
        doi_value = self.get_doi_value(record)
        if doi_value and not make_findable:
            return
        errors = self.mapping.metadata_check(record)
        if errors:
            raise ValidationError(message=errors)
        self.initialize_client(record)

        doi = self.generate_doi(record)

        self.upload_to_datacite(record,doi, make_findable)

        self.create_pid(record, doi)
        self.add_doi_value(record, doi)
        if make_findable:
            try:
                pid_value = self.get_pid_doi_value(record)
                pid_value.register()
            except:
                pass
    def upload_to_datacite(self, record, doi, make_findable = False):
        client = self.initialize_client(record)
        record = self.add_links(record)

        payload = self.mapping.create_datacite_payload(record)
        request_metadata = {"data": {"type": "dois", "attributes": {}}}
        request_metadata["data"]["attributes"] = payload

        request_metadata["data"]["attributes"]["doi"] = doi
        if make_findable:
            request_metadata["data"]["attributes"]["event"] = "publish"

        client.datacite_request(request_metadata, record, doi, "PUT")

    def update(self, record):
        """Update existing DOI."""
        doi_value = self.get_doi_value(record)
        if not doi_value:
            return
        errors = self.mapping.metadata_check(record)
        if errors:
            raise ValidationError(message=errors)
        self.initialize_client(record)

        doi = self.generate_doi(record)

        self.upload_to_datacite(record, doi)


    def publish(self, record):
        """Publish existing doi."""
        doi_value = self.get_doi_value(record)
        if not doi_value:
            return
        errors = self.mapping.metadata_check(record)
        if errors:
            raise ValidationError(message=errors)
        self.initialize_client(record)

        doi = self.generate_doi(record)

        self.upload_to_datacite(record, doi, True)

    def delete(self, record):
        pid_value = self.get_pid_doi_value(record)
        if not pid_value:
            return

        client = self.initialize_client(record)
        doi = self.generate_doi(record)
        if hasattr(record, "is_published") and record.is_published:
            request_metadata = {"data": {"type": "dois", "attributes": {"event": "hide"}}}

            client.datacite_request(request_metadata, record,doi,  "PUT")
            pid_value.delete()
            self.remove_doi_value(record)
        else:
            client.datacite_request({}, record,doi, method="DELETE")
            pid_value.unassign()
            pid_value.delete()
            self.remove_doi_value(record)

    def delete_canonical(self, record):
        doi_value = self.get_doi_value(record.parent)
        if not doi_value:
            return False
        doi_versions = get_doi_versions(record)

        client = self.initialize_client(record)
        doi = self.generate_doi(record.parent)
        if len(doi_versions) == 0:
            pid_value = self.get_pid_doi_value(record.parent)
            request_metadata = {"data": {"type": "dois", "attributes": {"event": "hide"}}}
            client.datacite_request(request_metadata,record, doi, "PUT")
            pid_value.delete()
            self.remove_doi_value(record.parent)
            return True
        return False

    def create_canonical(self, record):
        latest = get_latest(record)

        if not latest:
            return False

        doi_value = self.get_doi_value(record.parent)
        if doi_value:
            return  False

        errors = self.mapping.metadata_check(latest)
        if errors:
            raise ValidationError(message=errors)

        self.initialize_client(record)

        doi = self.generate_doi(record.parent)

        self.upload_to_datacite(latest, doi, make_findable = True)

        self.create_pid(record.parent, doi)
        self.add_doi_value(record.parent, doi)
        try:
            pid_value = self.get_pid_doi_value(record.parent)
            pid_value.register()
        except:
            pass
        return True

    def update_canonical(self, record):
        latest = get_latest(record)
        if not latest:
            return

        doi_value = self.get_doi_value(record.parent)

        if not doi_value:
            return

        errors = self.mapping.metadata_check(latest)
        if errors:
            raise ValidationError(message=errors)
        self.initialize_client(record)

        doi = self.generate_doi(record.parent)

        self.upload_to_datacite(latest, doi)


