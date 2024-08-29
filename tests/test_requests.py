

def test_datacite_config(app):
    assert app.config["DATACITE_URL"] == 'https://api.datacite.org/dois'

    assert "DATACITE_PREFIX" in app.config

def link_api2testclient(api_link):
    base_string = "https://127.0.0.1:5000/api/"
    return api_link[len(base_string) - 1 :]


def test_edit_autoaccept(
    logged_client,
    users,
    urls,
    create_doi_data_function,
    record_factory,
    search_clear,
):
    creator = users[0]
    creator_client = logged_client(creator)

    record1 = record_factory(creator.identity)
    id_ = record1["id"]

    # test direct edit is forbidden
    direct_edit = creator_client.post(
        f"{urls['BASE_URL']}{id_}/draft",
    )
    assert direct_edit.status_code == 403

    resp_request_create = creator_client.post(
        urls["BASE_URL_REQUESTS"],
        json=create_doi_data_function(record1["id"]),
    )
    resp_request_submit = creator_client.post(
        link_api2testclient(resp_request_create.json["links"]["actions"]["submit"]),
    )
    # is request accepted and closed?
    request = creator_client.get(
        f'{urls["BASE_URL_REQUESTS"]}{resp_request_create.json["id"]}',
    ).json

    assert request["status"] == "accepted"
    assert not request["is_open"]
    assert request["is_closed"]

    assert "draft_record:links:self" in request["payload"]
    assert "draft_record:links:self_html" in request["payload"]

    # ThesisRecord.index.refresh()
    # ThesisDraft.index.refresh()
    # edit action worked?
    # search = creator_client.get(
    #     f'user{urls["BASE_URL"]}',
    # ).json[
    #     "hits"
    # ]["hits"]
    # assert len(search) == 1
    # assert search[0]["links"]["self"].endswith("/draft")
    # assert search[0]["id"] == id_
    #
    

