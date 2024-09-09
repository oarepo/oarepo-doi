from flask import current_app
from invenio_base.utils import obj_or_import_string
from marshmallow.exceptions import ValidationError
from oarepo_requests.actions.generic import OARepoAcceptAction, OARepoSubmitAction

from oarepo_doi.api import community_slug_for_credentials, create_doi


class CreateDoiAction(OARepoAcceptAction):
    log_event = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mode = current_app.config.get("DATACITE_MODE")
        self.url = current_app.config.get("DATACITE_URL")
        self.mapping = current_app.config.get("DATACITE_MAPPING")
        self.specified_doi = current_app.config.get("DATACITE_SPECIFIED_ID")

        self.username = None
        self.password = None
        self.prefix = None

    def credentials(self, community):
        credentials_def = current_app.config.get("DATACITE_CREDENTIALS")

        community_credentials = getattr(credentials_def, community, None)
        if (
            community_credentials is None
            and "DATACITE_CREDENTIALS_DEFAULT" in current_app.config
        ):
            community_credentials = current_app.config.get(
                "DATACITE_CREDENTIALS_DEFAULT"
            )
        self.username = community_credentials["username"]
        self.password = community_credentials["password"]
        self.prefix = community_credentials["prefix"]

    def execute(self, identity, uow, *args, **kwargs):
        topic = self.request.topic.resolve()
        slug = community_slug_for_credentials(topic.parent["communities"]["default"])

        self.credentials(slug)

        if topic.is_draft:
            create_doi(self, topic, topic, None)
        else:
            create_doi(self, topic, topic, "publish")
        super().execute(identity, uow)


class ValidateDataForDoiAction(OARepoSubmitAction):
    log_event = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mapping = current_app.config.get("DATACITE_MAPPING")

    def execute(self, identity, uow, *args, **kwargs):
        topic = self.request.topic.resolve()
        mapping = obj_or_import_string(self.mapping[topic.schema])()
        errors = mapping.metadata_check(topic)
        if len(errors) > 0:
            raise ValidationError(
                message=f"Could not assigned doi due to validation error: {errors} "
            )

        super().execute(identity, uow)
