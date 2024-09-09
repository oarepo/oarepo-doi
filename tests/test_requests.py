from invenio_access.permissions import system_identity
from invenio_base.utils import obj_or_import_string


def test_datacite_config(app):
    assert app.config["DATACITE_URL"] == "https://api.datacite.org/dois"

    assert "DATACITE_PREFIX" in app.config
