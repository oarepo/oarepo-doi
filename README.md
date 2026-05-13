# OARepo DOI

OARepo DOI adds community-specific DOI configuration to OARepo/InvenioRDM
installations. It provides a DOI settings service and administration views, and
extends the DataCite PID provider so DOI registration can use credentials
configured for the record's default community.

## Features

- Stores DataCite credentials per community.
- Resolves DOI credentials from a record's default community.
- Falls back to the standard global DataCite configuration when no
  community-specific settings exist.
- Registers DOI settings in the Invenio administration interface.
- Keeps DataCite passwords encrypted in the database.

## Installation

The package is intended to be installed as part of an OARepo 14 based
application.

```bash
pip install oarepo-doi
```

## DOI Settings

Each DOI settings record connects a community to DataCite credentials:

- `community_slug`: slug of the community using these DOI credentials
- `prefix`: DataCite DOI prefix
- `username`: DataCite username
- `password`: DataCite password, stored encrypted

Only one DOI settings record can exist for a given community slug.

The service is registered under the `community-doi` service id and uses the
`doi-settings` search alias.

## REST API

The DOI settings resource is exposed under:

```text
/doi_settings
/doi_settings/<id>
```

The resource supports reading, updating and deleting DOI settings records.
Search, create, update and delete operations are protected by the DOI settings
permission policy and are available to system processes and administration
users.

Example payload:

```json
{
  "community_slug": "example-community",
  "prefix": "10.12345",
  "username": "datacite-user",
  "password": "datacite-password"
}
```

When a DOI settings record is created or updated, the referenced community must
exist. If the community slug cannot be found, the service returns a bad request.

## DataCite Integration

The package provides two record-aware DataCite classes:

- `oarepo_doi.services.providers.client:DataCiteRecordAwareClient`
- `oarepo_doi.services.providers.provider:DataCiteRecordAwareProvider`

The provider binds the current record to the DataCite client before DOI
generation, registration, update, restore and delete operations. The client then
looks up DOI settings for the record's default community.

When community DOI settings are found, DOI generation uses the community prefix
and the DataCite API client is created from the community username, password and
prefix. When no community DOI settings are found, the implementation falls back
to the standard InvenioRDM DataCite client and global `DATACITE_*`
configuration.

## Configuration

The DataCite client also respects the standard global DataCite configuration
when no community settings are available, including:

```python
DATACITE_PREFIX = "10.12345"
DATACITE_USERNAME = "user"
DATACITE_PASSWORD = "password"
DATACITE_FORMAT = "{prefix}/{id}"
DATACITE_TEST_MODE = True
```