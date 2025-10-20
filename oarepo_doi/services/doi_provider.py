from invenio_base.utils import obj_or_import_string
from oarepo_runtime.datastreams.utils import get_record_service_for_record
from invenio_access.permissions import system_identity
from invenio_pidstore.models import PersistentIdentifier
from marshmallow import ValidationError
from typing import Any
from flask import current_app
from invenio_pidstore.providers.base import BaseProvider
from invenio_db import db
from .relations import get_latest, get_doi_versions
from oarepo_doi.services.doi_client import DOIClient
import json

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


    def create(self, record, new = True, publish = False):
        doi_value = self.get_doi_value(record)
        if doi_value and new or not doi_value and not new:
            pass

        errors = self.mapping.metadata_check(record)
        if errors:
            raise ValidationError(message=errors)

        client = DOIClient()

        self.subcreate(record, publish, new)

    def subcreate(self, record, publish, new, canonical = False, canonical_rec = None):
        client = DOIClient()
        _, _, prefix = client.credentials(record)
        self.prefix = prefix

        record_service = get_record_service_for_record(record)
        if record_service is not None and hasattr(record_service, "links_item_tpl"):
            record["links"] = record_service.links_item_tpl.expand(system_identity, record)

            request_metadata: dict[str, Any] = {"data": {"type": "dois", "attributes": {}}}
            data = record
            if canonical_rec:
                data = canonical_rec
            payload = self.mapping.create_datacite_payload(data)
            request_metadata["data"]["attributes"] = payload

            if canonical:
                record = record.parent
            doi = self.generate_doi(record)
            request_metadata["data"]["attributes"]["doi"] = doi

            if publish:
                request_metadata["data"]["attributes"]["event"] = "publish"
            response = client.datacite_request(request_metadata, record, "PUT")

            if new:
                self.create_pid(record, doi)
                self.add_doi_value(record, doi)
            elif publish and not new:
                try:
                    pid_value = self.get_pid_doi_value(record) #todo what it does not exists yet
                    pid_value.register()
                except:
                    pass

            return True

        return None

    def delete(self, record, canonical = False):
        pid_value = self.get_pid_doi_value(record)
        if not pid_value:
            return

        client = DOIClient()

        if canonical or (hasattr(record, "is_published") and record.is_published):
            request_metadata = {"data": {"type": "dois", "attributes": {"event": "hide"}}}
            client.datacite_request(request_metadata, record, "PUT")
            pid_value.delete()
            self.remove_doi_value(record)
        else:
            client.datacite_request({}, record, method="DELETE")
            pid_value.unassign()
            pid_value.delete()
            self.remove_doi_value(record)

    def delete_canonical(self, record):
        doi_value = self.get_doi_value(record.parent)
        if not doi_value:
            return
        doi_versions = get_doi_versions(record)
        if len(doi_versions) == 0:
            self.delete(record.parent, canonical=True)

    def create_canonical(self, record, new):
        latest = get_latest(record)
        if not latest:
            return
        self.subcreate(record, publish=True, new=new, canonical=True, canonical_rec = latest)

