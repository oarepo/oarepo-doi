from invenio_requests.customizations import actions
from flask import current_app
from oarepo_doi.api import create_doi, edit_doi

class CreateDoiAction(actions.CreateAction):
    log_event = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mode = current_app.config.get("DATACITE_MODE")
        self.url = current_app.config.get("DATACITE_URL")
        self.mapping = current_app.config.get("DATACITE_MAPPING")

        self.username = None
        self.password = None
        self.prefix = None

    def credentials(self, community):
        credentials_def = current_app.config.get("DATACITE_CREDENTIALS")

        community_credentials = getattr(credentials_def, community, None)
        if community_credentials is None and "DATACITE_CREDENTIALS_DEFAULT" in current_app.config:
            community_credentials = current_app.config.get("DATACITE_CREDENTIALS_DEFAULT")
        self.username = community_credentials["username"]
        self.password = community_credentials["password"]
        self.prefix = community_credentials["prefix"]

    def execute(self, identity, uow, *args, **kwargs):

        topic = self.request.topic.resolve()
        self.credentials(topic['parent']['communities']['default'])

        if topic.is_draft:
            create_doi(self, topic, topic["metadata"], None)
        else:
            create_doi(self, topic, topic["metadata"], "publish")
        super().execute(identity, uow)


class EditDoiAction(actions.AcceptAction):
    log_event = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mode = current_app.config.get("DATACITE_MODE")
        self.url = current_app.config.get("DATACITE_URL")
        self.mapping = current_app.config.get("DATACITE_MAPPING")

        self.username = None
        self.password = None
        self.prefix = None

    def credentials(self, community):
        credentials_def = current_app.config.get("DATACITE_CREDENTIALS")

        community_credentials = getattr(credentials_def, community, None)
        if community_credentials is None and "DATACITE_CREDENTIALS_DEFAULT" in current_app.config:
            community_credentials = current_app.config.get("DATACITE_CREDENTIALS_DEFAULT")
        self.username = community_credentials["username"]
        self.password = community_credentials["password"]
        self.prefix = community_credentials["prefix"]

    def execute(self, identity, uow, *args, **kwargs):

        topic = self.request.topic.resolve()
        self.credentials(topic['parent']['communities']['default'])
        if topic.is_draft:
            edit_doi(self, topic, None)
        else:
            edit_doi(self, topic, "publish")

        super().execute(identity, uow)