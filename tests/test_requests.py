from invenio_access.permissions import system_identity
from invenio_base.utils import obj_or_import_string



def test_datacite_config(app):
    assert app.config["DATACITE_URL"] == 'https://api.datacite.org/dois'

    assert "DATACITE_PREFIX" in app.config




# def test_request(app, client_with_login):
#     with client_with_login.get(f"/thesis/") as c:
#         assert c.status_code == 200
#
#
# def test_create(app, db, record_service, sample_metadata_list, search_clear):
#     created_records = []
#     for sample_metadata_point in sample_metadata_list:
#         created_records.append(
#             record_service.create(system_identity, sample_metadata_point)
#         )
#     for sample_metadata_point, created_record in zip(
#         sample_metadata_list, created_records
#     ):
#         created_record_reread = record_service.read(
#             system_identity, created_record["id"]
#         )
#         assert (
#             created_record_reread.data["metadata"] == sample_metadata_point["metadata"]
#         )
