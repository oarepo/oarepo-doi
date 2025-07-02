"""Results for the oai_runs service."""

from invenio_records_resources.services.records.results import RecordItem, RecordList


class CommunityDoiSettingsItem(RecordItem):
    """Single OAI Run result."""

    def __init__(
        self,
        service,
        identity,
        doi_settings,
        errors=None,
        links_tpl=None,
        schema=None,
        **kwargs,
    ):
        """Constructor."""
        self._data = None
        self._errors = errors
        self._identity = identity
        self._doi_settings = doi_settings
        self._service = service
        self._links_tpl = links_tpl
        self._schema = schema or service.schema

    @property
    def id(self):
        """Identity of the oai_run."""
        return str(self._doi_settings.id)

    @property
    def links(self):
        """Get links for this result item."""
        return self._links_tpl.expand(self._identity, self._doi_settings)

    @property
    def _obj(self):
        """Return the object to dump."""
        return self._doi_settings

    @property
    def data(self):
        """Property to get the oai_run."""
        if self._data:
            return self._data

        self._data = self._schema.dump(
            self._obj,
            context={
                "identity": self._identity,
                "record": self._doi_settings,
            },
        )

        if self._links_tpl:
            self._data["links"] = self.links

        return self._data



class CommunityDoiSettingsList(RecordList):
    """List of DOI settings results."""

