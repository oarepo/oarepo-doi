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


    def get_doi(self, record):
        """Extracts DOI from the record."""

        doi = None
        if "doi" in record["pids"]:
            doi = record["pids"]["doi"]
        return doi


    def add_doi(self, record, data, doi_value):
        """Adds a DOI to the record."""

        data["pids"]["doi"] = {"identifier": doi_value}

        record.update(data)
        record.commit()

    def remove_doi(self, record):
        """Removes DOI from the record."""

        if "doi" in record["pids"]:
            del record["pids"]["doi"]
        record.commit()
