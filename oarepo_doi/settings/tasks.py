"""Users service tasks."""

from celery import shared_task
from flask import current_app
from invenio_search.engine import search

from .proxies import current_doi_settings


@shared_task(ignore_result=True)
def reindex_domains(domain_ids):
    """Reindex the given  doi settings."""
    index = current_doi_settings.record_cls.index
    if current_doi_settings.indexer.exists(index):
        try:
            current_doi_settings.indexer.bulk_index(domain_ids)
        except search.exceptions.ConflictError as e:
            current_app.logger.warn(f"Could not bulk-reindex groups: {e}")


@shared_task(ignore_result=True)
def delete_domains(domain_ids):
    """Delete doi settings from index."""
    index = current_doi_settings.record_cls.index
    if current_doi_settings.indexer.exists(index):
        try:
            current_doi_settings.indexer.bulk_delete(domain_ids)
        except search.exceptions.ConflictError as e:
            current_app.logger.warn(f"Could not bulk-unindex groups: {e}")
