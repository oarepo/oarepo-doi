from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.facets.facets import TermsFacet


community_slug = TermsFacet(field="community_slug", label=_("Community slug"))
username = TermsFacet(field="username", label=_("Username"))
prefix = TermsFacet(field="prefix", label=_("Prefix"))


