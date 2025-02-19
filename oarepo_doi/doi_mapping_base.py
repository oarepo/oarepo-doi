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

