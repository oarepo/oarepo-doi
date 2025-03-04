from abc import ABC, abstractmethod


class DataCiteMappingBase(ABC):

    @abstractmethod
    def metadata_check(self, data):
        """Checks metadata for required fields and returns errors if any."""
        pass

    @abstractmethod
    def create_datacite_payload(self, data):
        """Creates a DataCite payload from the given data."""
        pass


    def get_doi_value(self, record):
        """Extracts DOI from the record."""

        pids = record.get('pids', {})
        if pids is None:
            pids = {}
        doi = None
        if 'doi' in pids:
            doi = pids['doi']['identifier']
        return doi

    def add_doi_value(self, record, data, doi_value):
        """Adds a DOI to the record."""
        pids = record.get('pids', {})
        if pids is None:
            pids = {}
        pids["doi"] = {"provider": "datacite", "identifier": doi_value}
        try:
            data.pids = pids
        except:
            data["pids"] = pids
        record.update(data)
        record.commit()

    def remove_doi_value(self, record):
        """Removes DOI from the record."""
        pids = record.get('pids', {})
        if pids is None:
            pids = {}
        if "doi" in pids:
            pids.pop("doi")
        record.commit()
