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

    def __getitem__(self, key):
        """Key a key from the data."""
        return self.data[key]

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

    @property
    def errors(self):
        """Get the errors."""
        return self._errors

    def to_dict(self):
        """Get a dictionary for the oai_run."""
        res = self.data
        if self._errors:
            res["errors"] = self._errors
        return res


class CommunityDoiSettingsList(RecordList):
    """List of OAI Run results."""

    @property
    def hits(self):
        """Iterator over the hits."""
        doi_settings_cls = self._service.record_cls

        for hit in self._results:
            # load dump
            doi_settings = doi_settings_cls.loads(hit.to_dict())
            schema = self._service.schema

            # project the oai_run
            projection = schema.dump(
                doi_settings,
                context={
                    "identity": self._identity,
                    "record": doi_settings,
                },
            )

            # inject the links
            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(
                    self._identity, doi_settings
                )

            yield projection

    def to_dict(self):
        """Return result as a dictionary."""
        # TODO: This part should imitate the result item above. I.e. add a
        # "data" property which uses a ServiceSchema to dump the entire object.
        res = {
            "hits": {
                "hits": list(self.hits),
                "total": self.total,
            }
        }

        if self.aggregations:
            res["aggregations"] = self.aggregations

        if self._params:
            res["sortBy"] = self._params["sort"]
            if self._links_tpl:
                res["links"] = self._links_tpl.expand(self._identity, self.pagination)

        return res
