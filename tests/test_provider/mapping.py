from oarepo_runtime.i18n import lazy_gettext as _

missing_data_message = _("Missing data for required field.")


class TestMapping:
    def metadata_check(self, data):
        errors = {}
        data = data["metadata"]
        if "title" not in data:
            errors["metadata.title"] = [missing_data_message]
        if "publishers" not in data:
            errors["metadata.publishers"] = [missing_data_message]
        return errors

    def create_datacite_payload(self, data):
        payload = {}

        metadata = data["metadata"]
        payload["titles"] = metadata["title"]

        return payload
