from invenio_requests.customizations import SubmitAction
from invenio_requests.resolvers.registry import ResolverRegistry
from invenio_records_resources.proxies import current_service_registry

from oarepo_doi.api import create_doi


class DoiDraftAction(SubmitAction):
    def execute(self, identity, uow):
        topic = self.request.topic.resolve()
        # create_doi(topic, event=None)
        super().execute(identity, uow)
