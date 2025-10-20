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
            if not record.is_published:
                self.provider.create(record=record, new=False, publish=False)
                self.provider.create_canonical(record=record, new=False)
            else:
                self.provider.create(record=record, new=False, publish=False)
                self.provider.create_canonical(record=record, new=False)
            update_doi_relations(record)
    def update(self, identity, data=None, record=None, **kwargs):
        if not DOIClient().credentials(
                record=record,
        ):
            return
        if self.provider.get_doi_value(record):
            self.provider.create(record=record, new=False, publish=False)
            self.provider.create_canonical(record=record, new=False)

            update_doi_relations(record)
    def publish(self, identity, data=None, record=None, draft=None, **kwargs):
        if not DOIClient().credentials(
                record=record,
        ):
            return
        if self.provider.get_doi_value(record):
            new = False if self.provider.get_doi_value(record) else True
            self.provider.create(record=record, new=new, publish=True)
            new = False if self.provider.get_doi_value(record.parent) else True
            self.provider.create_canonical(record=record, new=new)

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
        self.provider.delete_canonical(record,)
        self.provider.create_canonical(record, new = False)
        update_doi_relations(record)

    def delete_draft(self, identity, draft=None, record=None, force=False):
        if not DOIClient().credentials(
                draft
        ):
            return

        self.provider.delete(draft)
        self.provider.delete_canonical(draft)
        self.provider.create_canonical(draft, new = False)
        update_doi_relations(draft)


