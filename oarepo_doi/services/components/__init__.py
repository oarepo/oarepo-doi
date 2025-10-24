from flask import current_app
from invenio_records_resources.services.records.components import ServiceComponent
from ..doi_provider import DOIProvider
from ..doi_client import DOIClient
from ..relations import update_doi_relations

class DoiComponent(ServiceComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.provider = DOIProvider()

    def update_draft(self, identity, data=None, record=None, **kwargs):
        if not DOIClient().credentials(
                record=record,
        ):
            return
        if self.provider.get_doi_value(record):
            self.provider.update(record=record)
            self.provider.update_canonical(record=record)

            update_doi_relations(record)

    def update(self, identity, data=None, record=None, **kwargs):
        if not DOIClient().credentials(
                record=record,
        ):
            return
        if self.provider.get_doi_value(record):
            self.provider.update(record=record)
            self.provider.update_canonical(record=record)

            update_doi_relations(record)

    def publish(self, identity, data=None, record=None, draft=None, **kwargs):
        if not DOIClient().credentials(
                record=record,
        ):
            return
        if self.provider.get_doi_value(record):
            self.provider.create(record=record, make_findable=True)
            created = self.provider.create_canonical(record=record)
            if not created:
                self.provider.update_canonical(record=record)
            update_doi_relations(record)

    def new_version(self, identity, draft=None, record=None, **kwargs):
        """Update draft metadata."""
        doi_value = self.provider.get_doi_value(draft)
        if doi_value is not None:
            self.provider.remove_doi_value(draft)

    def delete_record(self, identity,  record=None, **kwargs):
        if not DOIClient().credentials(
                record=record,
        ):
            return
        self.provider.delete(record)
        deleted = self.provider.delete_canonical(record)
        if not deleted:
            self.provider.update_canonical(record)
        update_doi_relations(record)

    def delete_draft(self, identity, draft=None, record=None, force=False):
        if not DOIClient().credentials(
                draft
        ):
            return

        self.provider.delete(draft)
        deleted = self.provider.delete_canonical(draft)
        if not deleted:
            self.provider.update_canonical(draft)
        update_doi_relations(draft)


