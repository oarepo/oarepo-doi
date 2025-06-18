
from oarepo_doi.services.provider import OarepoDataCitePIDProvider

class ThesisTestDataCitePIDProvider(OarepoDataCitePIDProvider):
    def create_datacite_payload(self, data):
        metadata = data["metadata"]
        payload = {}

        return payload

    def validate(self, record, identifier=None, provider=None, **kwargs):
        """Validate the attributes of the identifier."""

        return True, []

    def metadata_check(self, record, schema=None, provider=None, **kwargs):

        errors = {}

        return errors


    def credentials(self, record):
        return "test", "test", "1234"

    def create_and_reserve(self, record, **kwargs):
        pass

    def delete(self, record, **kwargs):
        pass