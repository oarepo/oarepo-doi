from typing import Protocol


class DataCiteMappingProtocol(Protocol):
    def metadata_check(self, data, errors=[]) -> []:
        ...

    def create_datacite_payload(self, data) -> None:
        ...

    def get_doi(self, record) -> {}:
        ...

    def add_doi(self, record, data, doi_value) -> None:
        ...
