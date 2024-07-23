from invenio_requests.customizations import actions
from flask import current_app
from oarepo_doi.api import create_doi

class CreateDoiAction(actions.AcceptAction):
    log_event = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.username = current_app.config.get("DATACITE_USERNAME")
        self.password = current_app.config.get("DATACITE_PASSWORD")
        self.url = current_app.config.get("DATACITE_URL")
        self.prefix = current_app.config.get("DATACITE_PREFIX")
        self.mapping = current_app.config.get("DATACITE_MAPPING")

    def execute(self, identity, uow, *args, **kwargs):

        topic = self.request.topic.resolve()
        if topic.is_draft:
            create_doi(self, topic, topic["metadata"], None)
        else:
            create_doi(self, topic, topic["metadata"], "publish")
        super().execute(identity, uow)


class EditDoiAction(actions.AcceptAction):
    log_event = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.username = current_app.config.get("DATACITE_USERNAME")
        self.password = current_app.config.get("DATACITE_PASSWORD")
        self.url = current_app.config.get("DATACITE_URL")
        self.prefix = current_app.config.get("DATACITE_PREFIX")
        self.mapping = current_app.config.get("DATACITE_MAPPING")

    def execute(self, identity, uow, *args, **kwargs):

        topic = self.request.topic.resolve()

        if topic.is_draft:
            edit_doi(self, topic, None)
        else:
            edit_doi(self, topic, "publish")

        super().execute(identity, uow)