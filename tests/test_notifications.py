def test_submit_notifications(
    app,
    users,
    logged_client,
    draft_factory,
    submit_request_on_draft,
    link2testclient,
    urls,
):
    mail = app.extensions.get("mail")
    assert mail

    creator = users[0]
    receiver = users[1]
    receiver_client = logged_client(receiver)

    draft1 = draft_factory(creator.identity)

    with mail.record_messages() as outbox:
        resp_request_submit = submit_request_on_draft(
            creator.identity, draft1["id"], "assign_doi"
        )
        # check notification is build on submit
        assert len(outbox) == 1
        sent_mail = outbox[0]
        assert 'Request to assign DOI to record blabla' in sent_mail.subject
        assert 'You have been asked to approve a DOI assignment for the record "blabla"' in sent_mail.body
        assert 'You have been asked to approve a DOI assignment for the record "blabla"' in sent_mail.html


def test_accept_notifications(
    app,
    users,
    logged_client,
    draft_factory,
    submit_request_on_draft,
    link2testclient,
    urls,
):
    mail = app.extensions.get("mail")
    receiver = users[1]
    receiver_client = logged_client(receiver)
    assert mail

    creator = users[0]
    draft1 = draft_factory(creator.identity)
    draft1_id = draft1["id"]
    resp_request_submit = submit_request_on_draft(
        creator.identity, draft1["id"], "assign_doi"
    )
    record = receiver_client.get(f"{urls['BASE_URL']}{draft1_id}/draft?expand=true")
    with mail.record_messages() as outbox:
        accept = receiver_client.post(
            link2testclient(
                record.json["expanded"]["requests"][0]["links"]["actions"]["accept"]
            ),
        )
        # check notification is build on submit
        assert len(outbox) == 1
        sent_mail = outbox[0]

        assert "DOI assignment request for 'blabla' has been approved" in sent_mail.subject
        assert 'Your request to assign a DOI to the record "blabla" has been approved. You can view the updated record at' in sent_mail.body
        assert 'Your request to assign a DOI to the record "blabla" has been approved. You can view the updated record at' in sent_mail.html


def test_decline_notifications(
    app,
    users,
    logged_client,
    draft_factory,
    submit_request_on_draft,
    link2testclient,
    urls,
):
    mail = app.extensions.get("mail")
    receiver = users[1]
    receiver_client = logged_client(receiver)
    assert mail

    creator = users[0]
    draft1 = draft_factory(creator.identity)
    draft1_id = draft1["id"]
    resp_request_submit = submit_request_on_draft(
        creator.identity, draft1["id"], "assign_doi"
    )
    record = receiver_client.get(f"{urls['BASE_URL']}{draft1_id}/draft?expand=true")

    with mail.record_messages() as outbox:
        decline = receiver_client.post(
            link2testclient(
                record.json["expanded"]["requests"][0]["links"]["actions"]["decline"]
            ),
        )
        # check notification is build on decline
        assert len(outbox) == 1
        sent_mail = outbox[0]
        assert "Request for DOI assignment to record 'blabla' was declined" in sent_mail.subject
        assert 'Request for assigning a DOI to the record "blabla" was declined'  in sent_mail.body
        assert 'Request for assigning a DOI to the record "blabla" was declined' in sent_mail.html


def test_accept_delete_notifications(
    app,
    users,
    logged_client,
    draft_factory,
    submit_request_on_draft,
    link2testclient,
    urls,
):
    mail = app.extensions.get("mail")
    receiver = users[1]
    receiver_client = logged_client(receiver)
    assert mail

    creator = users[0]
    draft1 = draft_factory(creator.identity)
    draft1_id = draft1["id"]
    resp_request_submit = submit_request_on_draft(
        creator.identity, draft1["id"], "assign_doi"
    )
    record = receiver_client.get(f"{urls['BASE_URL']}{draft1_id}/draft?expand=true")
    accept = receiver_client.post(
        link2testclient(
            record.json["expanded"]["requests"][0]["links"]["actions"]["accept"]
        ),
    )
    with mail.record_messages() as outbox:
        resp_request_submit = submit_request_on_draft(
            creator.identity, draft1["id"], "delete_doi"
        )
        # check notification is build on decline
        assert len(outbox) == 1
        sent_mail = outbox[0]
        assert "Request to delete DOI from record blabla" in sent_mail.subject
        assert 'You have been asked to approve a DOI deletion for the record "blabla".'  in sent_mail.body
        assert 'You have been asked to approve a DOI deletion for the record "blabla".' in sent_mail.html

    record = receiver_client.get(f"{urls['BASE_URL']}{draft1_id}/draft?expand=true")

    with mail.record_messages() as outbox:
        accept = receiver_client.post(
            link2testclient(
                record.json["expanded"]["requests"][0]["links"]["actions"]["accept"]
            ),
        )
        # check notification is build on decline
        assert len(outbox) == 1
        sent_mail = outbox[0]
        assert "DOI deletion request for 'blabla' has been approved" in sent_mail.subject
        assert 'Your request to delete the DOI from the record "blabla" has been approved.'  in sent_mail.body
        assert 'Your request to delete the DOI from the record "blabla" has been approved.' in sent_mail.html

def test_decline_delete_notifications(
    app,
    users,
    logged_client,
    draft_factory,
    submit_request_on_draft,
    link2testclient,
    urls,
):
    mail = app.extensions.get("mail")
    receiver = users[1]
    receiver_client = logged_client(receiver)
    assert mail

    creator = users[0]
    draft1 = draft_factory(creator.identity)
    draft1_id = draft1["id"]
    resp_request_submit = submit_request_on_draft(
        creator.identity, draft1["id"], "assign_doi"
    )
    record = receiver_client.get(f"{urls['BASE_URL']}{draft1_id}/draft?expand=true")
    accept = receiver_client.post(
        link2testclient(
            record.json["expanded"]["requests"][0]["links"]["actions"]["accept"]
        ),
    )
    resp_request_submit = submit_request_on_draft(
        creator.identity, draft1["id"], "delete_doi"
    )
    record = receiver_client.get(f"{urls['BASE_URL']}{draft1_id}/draft?expand=true")

    with mail.record_messages() as outbox:
        accept = receiver_client.post(
            link2testclient(
                record.json["expanded"]["requests"][0]["links"]["actions"]["decline"]
            ),
        )
        # check notification is build on decline
        assert len(outbox) == 1
        sent_mail = outbox[0]
        assert "Request for DOI deletion from record 'blabla' was declined" in sent_mail.subject
        assert 'Request for deleting the DOI from the record "blabla" was declined.'  in sent_mail.body
        assert 'Request for deleting the DOI from the record "blabla" was declined.' in sent_mail.html
