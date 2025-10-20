from flask import current_app
from invenio_records_resources.services.records.components import ServiceComponent
from ..doi_provider import DOIProvider
from ..doi_client import DOIClient
from ..relations import update_doi_relations

class DoiComponent(ServiceComponent):




    def update_draft(self, identity, data=None, record=None, **kwargs):
        if not DOIClient().credentials(
                record=record,
        ):
            return
        provider = DOIProvider()
        if provider.get_doi_value(record):
            if not record.is_published:
                provider.create(record=record, new=False, publish=False)
                provider.create_canonical(record=record, new=False)
            else:
                provider.create(record=record, new=False, publish=False)
                provider.create_canonical(record=record, new=False)
            update_doi_relations(record)
    def update(self, identity, data=None, record=None, **kwargs):
        if not DOIClient().credentials(
                record=record,
        ):
            return
        provider = DOIProvider()
        if provider.get_doi_value(record):
            provider.create(record=record, new=False, publish=False)
            provider.create_canonical(record=record, new=False)

            update_doi_relations(record)
    def publish(self, identity, data=None, record=None, draft=None, **kwargs):
        if not DOIClient().credentials(
                record=record,
        ):
            return
        provider = DOIProvider()
        if provider.get_doi_value(record):
            new = False if provider.get_doi_value(record) else True
            provider.create(record=record, new=new, publish=True)
            new = False if provider.get_doi_value(record.parent) else True
            provider.create_canonical(record=record, new=new)

            update_doi_relations(record)
    def new_version(self, identity, draft=None, record=None, **kwargs):
        """Update draft metadata."""
        provider = DOIProvider()
        doi_value = provider.get_doi_value(draft)
        if doi_value is not None:
            provider.remove_doi_value(draft)

    def delete_record(self, identity,  record=None, **kwargs):
        if not DOIClient().credentials(
                record=record,
        ):
            return
        provider = DOIProvider()
        provider.delete(record)
        provider.delete_canonical(record,)
        provider.create_canonical(record, new = False)
        update_doi_relations(record)

    def delete_draft(self, identity, draft=None, record=None, force=False):
        if not DOIClient().credentials(
                draft
        ):
            return
        provider = DOIProvider()
        provider.delete(draft)
        provider.delete_canonical(draft)
        provider.create_canonical(draft, new = False)
        update_doi_relations(draft)


