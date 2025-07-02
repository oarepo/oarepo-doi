from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils.types import UUIDType
from invenio_db import db

from invenio_communities.communities.records.models import CommunityMetadata
import uuid
from invenio_users_resources.records.models import AggregateMetadata
from sqlalchemy_utils import  Timestamp
from sqlalchemy_utils import EncryptedType
from invenio_oauthclient.models import _secret_key

class CommunityDoiSettings(db.Model, Timestamp):
    """Model for Community DOI settings."""

    __tablename__ = "community_doi_settings"

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )

    @declared_attr
    def community_slug(cls):

        return db.Column(
            db.String(255),
            db.ForeignKey(CommunityMetadata.slug, ondelete="CASCADE"),
            unique=True,
        )

    prefix = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column( EncryptedType(type_in=db.Text, key=_secret_key), nullable=False)

class CommunityDoiSettingsAggregateModel(AggregateMetadata):

    _properties = [
        "id",
        "community_slug",
        "prefix",
        "username",
        "password",
        "created",
        "updated",
    ]
    """Properties of this object that can be accessed."""

    _set_properties = [
        "community_slug",
        "prefix",
        "username",
        "password",
    ]
    """Properties of this object that can be set."""

    @property
    def model_obj(self):
        """The actual model object behind this user aggregate."""
        if self._model_obj is None:
            id_ = self._data.get("id")
            with db.session.no_autoflush:
                self._model_obj = CommunityDoiSettings.query.get(id_)
        return self._model_obj

    @property
    def version_id(self):
        """Return the version ID of the record."""
        return 1


