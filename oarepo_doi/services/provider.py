import json
import warnings
from collections import ChainMap
from json import JSONDecodeError
import uuid
from invenio_communities import current_communities
from invenio_search.engine import dsl
from datacite.errors import (
    DataCiteNoContentError,
    DataCiteServerError,
)
from invenio_db import db
from invenio_pidstore.providers.base import BaseProvider
import requests
from oarepo_runtime.datastreams.utils import get_record_service_for_record

from marshmallow.exceptions import ValidationError
from flask import current_app

from invenio_pidstore.models import PIDStatus
from invenio_rdm_records.services.pids.providers import DataCiteClient

from invenio_rdm_records.services.pids.providers.base import PIDProvider
from invenio_access.permissions import system_identity
from invenio_pidstore.models import PersistentIdentifier

class OarepoDataCitePIDProvider(PIDProvider):
    """DataCite Provider class.

    Note that DataCite is only contacted when a DOI is reserved or
    registered, or any action posterior to it. Its creation happens
    only at PIDStore level.
    """

    def __init__(
        self,
        id_,
        client=None,
        serializer=None,
        pid_type="doi",
        default_status=PIDStatus.NEW,
        **kwargs,
    ):
        """Constructor."""
        super().__init__(
            id_,
            client=(client or DataCiteClient("datacite", config_prefix="DATACITE")),
            pid_type=pid_type,
            default_status=default_status,
        )
        self.serializer = serializer
        self.username = None
        self.password = None
        self.prefix = None

    @property
    def mode(self):
        return current_app.config.get("DATACITE_MODE")

    @property
    def url(self):
        return current_app.config.get("DATACITE_URL")

    @property
    def specified_doi(self):
        return current_app.config.get("DATACITE_SPECIFIED_ID")

    def credentials(self, record):
        slug = self.community_slug_for_credentials(
            record.parent["communities"].get("default", None)
        )
        if not slug:
            credentials = current_app.config.get(
                "DATACITE_CREDENTIALS_DEFAULT", None
            )
        else:
            credentials_def = current_app.config.get("DATACITE_CREDENTIALS")

            credentials = credentials_def.get(slug, None)
            if not credentials:
                credentials = current_app.config.get(
                    "DATACITE_CREDENTIALS_DEFAULT", None
                )
        if credentials is None:
            return False

        self.username = credentials["username"]
        self.password = credentials["password"]
        self.prefix = credentials["prefix"]

        return True

    @staticmethod
    def _log_errors(exception):
        """Log errors from DataCiteError class."""
        # DataCiteError will have the response msg as first arg
        ex_txt = exception.args[0] or ""
        if isinstance(exception, DataCiteNoContentError):
            current_app.logger.error(f"No content error: {ex_txt}")
        elif isinstance(exception, DataCiteServerError):
            current_app.logger.error(f"DataCite internal server error: {ex_txt}")
        else:
            # Client error 4xx status code
            try:
                ex_json = json.loads(ex_txt)
            except JSONDecodeError:
                current_app.logger.error(f"Unknown error: {ex_txt}")
                return

            # the `errors` field is only available when a 4xx error happened (not 500)
            for error in ex_json.get("errors", []):
                reason = error["title"]
                field = error.get("source")  # set when missing/wrong required field
                error_prefix = f"Error in `{field}`: " if field else "Error: "
                current_app.logger.error(f"{error_prefix}{reason}")

    def generate_id(self, record, **kwargs):
        """Generate a unique DOI."""
        pass #this is done on the datacite level

    @classmethod
    def is_enabled(cls, app):
        """Determine if datacite is enabled or not."""
        return True

    def can_modify(self, pid, **kwargs):
        """Checks if the PID can be modified."""
        return not pid.is_registered()

    def register(self, pid, record, **kwargs):
        """Register a DOI via the DataCite API.

        :param pid: the PID to register.
        :param record: the record metadata for the DOI.
        :returns: `True` if is registered successfully.
        """
        pass

    def community_slug_for_credentials(self, value):
        if not value:
            return None
        id_value = None
        slug = None
        try:
            id_value = uuid.UUID(value, version=4)
        except:
            slug = value
        if not slug:
            search = current_communities.service._search(
                "search",
                system_identity,
                {},
                None,
                extra_filter=dsl.Q("term", **{"id": value}),
            )
            community = search.execute()
            c = list(community.hits.hits)[0]
            return c._source.slug
        return slug

    def get_doi_value(self, record, parent = False):
        """Extracts DOI from the record."""
        if not parent:
            pids = record.get('pids', {})
        else:
            pids = record.parent.get('pids', {})
        if pids is None:
            pids = {}
        doi = None
        if 'doi' in pids:
            doi = pids['doi']['identifier']
        return doi

    def get_pid_doi_value(self, record, parent = False):
        """Extracts DOI from the record."""
        if not parent:
            id = record.id
        else:
            id = record.parent.id
        try:
            doi = PersistentIdentifier.get_by_object('doi', "rec", id)
            return doi
        except:
            return None

    def add_doi_value(self, record, data, doi_value, parent = False):
        """Adds a DOI to the record."""
        if not parent:
            pids = record.get('pids', {})
        else:
            pids = record.parent.get('pids', {})
        if pids is None:
            pids = {}
        pids["doi"] = {"provider": "datacite", "identifier": doi_value}

        if not parent:
            data.pids = pids
            record.update(data)
            record.commit()
        else:
            data.parent.pids = pids
            record.update(data)
            record.parent.commit()


    def remove_doi_value(self, record):
        """Removes DOI from the record."""
        pids = record.get('pids', {})
        if pids is None:
            pids = {}
        if "doi" in pids:
            pids.pop("doi")
        record.commit()

    def create(self, record, **kwargs):
        pass


    def datacite_request(self, record, **kwargs):
        """Create and reserve a DOI for the given record, and update the record with the reserved DOI."""
        doi_value = self.get_doi_value(record)
        if doi_value:
            raise ValidationError(
                message="DOI already associated with the record."
            )

        if not self.credentials(record):
            raise ValidationError(
                message="No credentials provided."
            )
        errors = self.metadata_check(record)
        record_service = get_record_service_for_record(record)
        record["links"] = record_service.links_item_tpl.expand(system_identity, record)

        if len(errors) > 0:
            raise ValidationError(
                message=errors
            )
        request_metadata = {"data": {"type": "dois", "attributes": {}}}

        payload = self.create_datacite_payload(record)
        request_metadata["data"]["attributes"] = payload
        if self.specified_doi:
            doi = f"{self.prefix}/{record['id']}"
            request_metadata["data"]["attributes"]["doi"] = doi
        if "event" in kwargs:
            # publish!!
            request_metadata["data"]["attributes"]["event"] = kwargs["event"]

        # request_metadata["data"]["attributes"]["event"] = "publish"
        request_metadata["data"]["attributes"]["prefix"] = str(self.prefix)
        return request_metadata


    def create_and_reserve(self, record, **kwargs):
        request_metadata = self.datacite_request(record, **kwargs)
        request = requests.post(
            url=self.url,
            json=request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(self.username, self.password),
        )

        if request.status_code != 201:
            raise requests.ConnectionError(
                "Expected status code 201, but got {}".format(request.status_code)
            )
        content =  request.content.decode("utf-8")



        json_content = json.loads(content)
        doi_value = json_content["data"]["id"]
        self.add_doi_value(record, record, doi_value)
        if "event" in kwargs:
            pid_status = 'R'  # registred
            parent_doi = self.get_pid_doi_value(record, parent=True)
            if parent_doi is None:
                self.register_parent_doi(record,request_metadata)
            elif parent_doi and record.versions.is_latest :
                self.update_parent_doi(record,request_metadata)

        else:
            pid_status = 'K'  # reserved


        BaseProvider.create('doi', doi_value, 'rec', record.id, pid_status)
        db.session.commit()



    def register_parent_doi(self, record, request_metadata):
        request_metadata["data"]["attributes"]["prefix"] = str(self.prefix)
        request_metadata["data"]["attributes"]["event"] = "publish"
        request = requests.post(
            url=self.url,
            json=request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(self.username, self.password),
        )

        if request.status_code != 201:
            raise requests.ConnectionError(
                "Expected status code 201, but got {}".format(request.status_code)
            )

        content = request.content.decode("utf-8")
        json_content = json.loads(content)
        doi_value = json_content["data"]["id"]
        pid_status = 'R'  # registred

        BaseProvider.create('doi', doi_value, 'rec', record.parent.id, pid_status)
        self.add_doi_value(record, record, doi_value, parent=True)
        db.session.commit()

    def update_parent_doi(self, record, request_metadata):
        if not self.url.endswith("/"):
            url = self.url + "/"
        else:
            url = self.url
        url = url + self.get_doi_value(record, parent= True).replace("/", "%2F")
        request = requests.put(
            url=url,
            json=request_metadata,
            headers={"Content-type": "application/vnd.api+json"},
            auth=(self.username, self.password),
        )

        if request.status_code != 200:
            raise requests.ConnectionError(
                "Expected status code 200, but got {}".format(request.status_code)
            )


    def update(self, record, url=None, **kwargs):


        doi_value = self.get_doi_value(record)
        if doi_value:
            if not self.credentials(record):
                raise ValidationError(
                    message="No credentials provided."
                )
            errors = self.metadata_check(record)
            record_service = get_record_service_for_record(record)
            record["links"] = record_service.links_item_tpl.expand(system_identity, record)
            if len(errors) > 0:
                raise ValidationError(
                    message=errors
                )
            if not self.url.endswith("/"):
                url = self.url + "/"
            else:
                url = self.url
            url = url + doi_value.replace("/", "%2F")

            request_metadata = {"data": {"type": "dois", "attributes": {}}}
            payload = self.create_datacite_payload(record)
            request_metadata["data"]["attributes"] = payload
            parent_doi = self.get_pid_doi_value(record, parent=True)
            if parent_doi is None and "event" in kwargs:
                self.register_parent_doi(record, request_metadata)
            elif parent_doi and record.versions.is_latest:
                self.update_parent_doi(record, request_metadata)
            if "event" in kwargs:
               request_metadata["data"]["attributes"]["event"] = kwargs["event"]


            request = requests.put(
                url=url,
                json=request_metadata,
                headers={"Content-type": "application/vnd.api+json"},
                auth=(self.username, self.password),
            )

            if request.status_code != 200:
                raise requests.ConnectionError(
                    "Expected status code 200, but got {}".format(request.status_code)
                )
            if "event" in kwargs:
                pid_value = self.get_pid_doi_value(record)
                if hasattr(pid_value, "status") and pid_value.status == "K":
                    pid_value.register()
    def restore(self, pid, **kwargs):
        """Restore previously deactivated DOI."""
        pass

    def delete(self, record, **kwargs):

        doi_value = self.get_doi_value(record)

        if not self.url.endswith("/"):
            url = self.url + "/"
        else:
            url = self.url
        url = url + doi_value.replace("/", "%2F")

        headers = {
            "Content-Type": "application/vnd.api+json"
        }

        if not self.credentials(record):
            raise ValidationError(
                message="No credentials provided."
            )

        response = requests.delete(url=url, headers=headers, auth=(self.username, self.password))

        if response.status_code != 204:
            raise requests.ConnectionError(
                "Expected status code 204, but got {}".format(response.status_code)
            )
        else:
            self.remove_doi_value(record)

    def create_datacite_payload(self, data):
        pass

    def validate(self, record, identifier=None, provider=None, **kwargs):
        """Validate the attributes of the identifier."""
        return True, []

    def metadata_check(self, record, schema=None, provider=None, **kwargs):
        pass

    def validate_restriction_level(self, record, identifier=None, **kwargs):
        """Remove the DOI if the record is restricted."""
        if record["access"]["record"] == "restricted":
            return False



