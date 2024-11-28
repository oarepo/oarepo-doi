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

        object_identifiers = record["metadata"].get("objectIdentifiers", [])
        doi = None
        for id in object_identifiers:
            if id.get("scheme") == "DOI":
                doi = id.get("identifier")
        return doi

    def add_doi(self, record, data, doi_value):
        """Adds a DOI to the record."""

        doi = {"scheme": "DOI", "identifier": doi_value}

        if "objectIdentifiers" in data["metadata"]:
            data["metadata"]["objectIdentifiers"].append(doi)
        else:
            data["metadata"]["objectIdentifiers"] = [doi]

        record.update(data)
        record.commit()

    def remove_doi(self, record):
        """Removes DOI from the record."""

        if "objectIdentifiers" in record["metadata"]:
            for id in record["metadata"]["objectIdentifiers"]:
                if id["scheme"] == "DOI":
                    record["metadata"]["objectIdentifiers"].remove(id)

        record.commit()
