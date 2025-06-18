from thesis.records.api import ThesisDraft, ThesisRecord


def test_submit_request(
    logged_client,
    users,
    urls,
    submit_request_on_draft,
    create_request_on_draft,
    draft_factory,
    link2testclient,
    search_clear,
):
    creator = users[0]


    draft1 = draft_factory(creator.identity)

    draft1_id = draft1["id"]

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    resp_request_submit = submit_request_on_draft(
        creator.identity, draft1_id, "assign_doi"
    )

    assert resp_request_submit.data["status"] == "submitted"

def test_accept_request(
    logged_client,
    users,
    urls,
    submit_request_on_draft,
    create_request_on_draft,
    draft_factory,
    link2testclient,
    search_clear,
):
    creator = users[0]
    receiver = users[1]

    creator_client = logged_client(creator)
    receiver_client = logged_client(receiver)

    draft1 = draft_factory(creator.identity)

    draft1_id = draft1["id"]

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    resp_request_submit = submit_request_on_draft(
        creator.identity, draft1_id, "assign_doi"
    )
    record = receiver_client.get(f"{urls['BASE_URL']}{draft1_id}/draft?expand=true")

    assert record.json["expanded"]["requests"][0]["links"]["actions"].keys() == {
        "accept",
        "decline",
    }
    asssign = receiver_client.post(
        link2testclient(
            record.json["expanded"]["requests"][0]["links"]["actions"]["accept"]
        ),
    )
    record = receiver_client.get(f"{urls['BASE_URL']}{draft1_id}/draft?expand=true")
    assert record.status_code == 200


def test_decline_request(
    logged_client,
    users,
    urls,
    submit_request_on_draft,
    create_request_on_draft,
    draft_factory,
    link2testclient,
    search_clear,
):
    creator = users[0]
    receiver = users[1]

    creator_client = logged_client(creator)
    receiver_client = logged_client(receiver)

    draft1 = draft_factory(creator.identity)

    draft1_id = draft1["id"]

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    resp_request_submit = submit_request_on_draft(
        creator.identity, draft1_id, "assign_doi"
    )
    record = receiver_client.get(f"{urls['BASE_URL']}{draft1_id}/draft?expand=true")

    assert record.json["expanded"]["requests"][0]["links"]["actions"].keys() == {
        "accept",
        "decline",
    }
    decline = receiver_client.post(
        link2testclient(
            record.json["expanded"]["requests"][0]["links"]["actions"]["decline"]
        ),
    )

    assert decline.status_code == 200

