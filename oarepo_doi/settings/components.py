from invenio_records_resources.services.records.components import ServiceComponent


class DoiSettingsComponent(ServiceComponent):
    """Service component"""

    def create(self, identity, data=None, record=None, errors=None, **kwargs):
        """Inject fields into the record."""
        record.prefix = data["prefix"]
        record.username = data["username"]
        record.password = data["password"]
        record.community_slug = data["community_slug"]

    def update(self, identity, data=None, record=None, **kwargs):
        # Required values
        record.prefix = data["prefix"]
        record.username = data["username"]
        record.password = data["password"]
        record.community_slug = data["community_slug"]

