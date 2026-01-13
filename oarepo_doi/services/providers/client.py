from invenio_rdm_records.services.pids.providers import DataCiteClient
from datacite import DataCiteRESTClient

from oarepo_doi.settings.models import CommunityDoiSettings
from invenio_db import db
from ..utils import community_slug_for_credentials


class DataCiteRecordAwareClient(DataCiteClient):
    """DataCite Client that stores record context."""

    def __init__(self, name, config_prefix=None, config_overrides=None, **kwargs):
        super().__init__(name, config_prefix, config_overrides, **kwargs)
        self._record = None

    def for_record(self, record):
        """Set record context and return self."""
        self._record = record
        return self

    @property
    def record(self):
        return self._record

    def check_credentials(self, **kwargs):
        pass  # todo ? + no need to call this if api is rewritten

    @property
    def api(self):
        """DataCite REST API client instance."""
        slug = community_slug_for_credentials(
            self.record.get("communities", {}).get("default", None)
        )

        doi_settings = (
            db.session.query(CommunityDoiSettings)
            .filter_by(community_slug=slug)
            .first()
        )
        self._api = DataCiteRESTClient(
            doi_settings.username,
            doi_settings.password,
            doi_settings.prefix,
            self.cfg("test_mode", True),
        )

        return self._api
