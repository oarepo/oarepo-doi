from invenio_records_resources.services.records.components import ServiceComponent
from invenio_communities.communities.records.models import CommunityMetadata

from invenio_i18n import lazy_gettext as _
from flask import abort

class DoiSettingsComponent(ServiceComponent):
    """Service component"""

    def create(self, identity, data=None, record=None, errors=None, **kwargs):
        """Inject fields into the record."""
        record.prefix = data["prefix"]
        record.username = data["username"]
        record.password = data["password"]
        record.community_slug = data["community_slug"]
        try:
            CommunityMetadata.query.filter_by(slug=data["community_slug"]).one()
        except:
            abort(400, description=_("Community not found"))
    def update(self, identity, data=None, record=None, **kwargs):
        # Required values
        record.prefix = data["prefix"]
        record.username = data["username"]
        record.password = data["password"]
        record.community_slug = data["community_slug"]
        try:
            CommunityMetadata.query.filter_by(slug=data["community_slug"]).one()
        except:
            abort(400, description=_("Community not found"))
