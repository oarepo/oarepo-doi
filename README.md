# OARepo DOI

`oarepo-doi` adds community-aware DataCite DOI handling to an OARepo/InvenioRDM
application. It provides an administration and REST interface for DOI settings,
then uses the settings selected for a record community when generating,
registering, updating or deleting a DOI.

## What it provides

- An administration panel module for creating and managing per-community
  DataCite credentials: DOI prefix, username, and encrypted password.
- A record-aware DataCite client and PID provider built on the standard Invenio
  DataCite implementations. They receive the current record's community
  context and select its corresponding credentials, with support for a `*`
  fallback setting.
- DOI configuration for both record DOI and parent/concept DOI providers.
- `OarepoDataciteJSONSerializer` for repositories with multiple record models;
  it selects the appropriate model-specific DataCite export at runtime.

## Requirements and installation

The package targets OARepo 14 and Python 3.14. In a standard OARepo
application, it is included through the `oarepo-app` dependency. Use either
the production or development extra as appropriate:

```
dependencies = [
   "oarepo-app[production]",
]
```

No separate `oarepo-doi` dependency is needed in that setup. Its entry points
register the extension, API blueprint, database model, Alembic migrations,
search mapping, administration views, and translations.

If you are integrating the package outside the standard OARepo application,
install it explicitly:

```bash
uv pip install oarepo-doi
```

After adding the package to an existing application, run that application
database migration workflow so that the `community_doi_settings` table is
created.

## How DOI settings are selected

When the provider handles a record, it resolves settings in this order:

1. Settings whose `community_slug` matches the record's default community.
2. The fallback settings record whose `community_slug` is `*`.
3. The standard InvenioRDM DataCite client and its global `DATACITE_*`
   configuration.

The selected settings supply the DataCite username, password, and DOI prefix.
DOI formatting continues to use the configured DataCite format. With the
default format, a generated DOI has the form `{prefix}/{id}`.

## Global DataCite fallback

Keep global DataCite configuration in the host application. It is used whenever
no matching community or `*` fallback setting exists. For example:

```python
DATACITE_PREFIX = "10.12345"
DATACITE_USERNAME = "datacite-user"
DATACITE_PASSWORD = "set-this-from-a-secret-store"
DATACITE_FORMAT = "{prefix}/{id}"
DATACITE_TEST_MODE = True
```

`DATACITE_TEST_MODE` is also used when a community-specific DataCite REST
client is created. If it is not configured as a boolean, the package defaults
to test mode.

## Multiple-model DataCite serialization

For an OARepo application with more than one record model, use
`OarepoDataciteJSONSerializer` on the DOI provider. It selects the model from
`current_runtime.rdm_models_by_schema` using `record.schema`. Every record model that can receive a DOI must define a
`datacite` export.



## DOI settings

Each settings record has these required fields:

| Field | Meaning |
| --- | --- |
| `community_slug` | Community slug, or `*` for the fallback settings record. |
| `prefix` | DataCite DOI prefix, for example `10.12345`. |
| `username` | DataCite account username. |
| `password` | DataCite account password. It is encrypted in the database and is not included in serialized record output. |

Only one settings record can exist for a particular `community_slug`. Creating settings for any slug other
than `*` requires that the corresponding community already exists.

Example community-specific payload:

```json
{
  "community_slug": "example-community",
  "prefix": "10.12345",
  "username": "datacite-user",
  "password": "datacite-password"
}
```

Example fallback payload:

```json
{
  "community_slug": "*",
  "prefix": "10.12345",
  "username": "datacite-user",
  "password": "datacite-password"
}
```

## REST API and permissions

The DOI settings resource is mounted at:

```text
/doi_settings
/doi_settings/<id>
```

It uses the standard record-resource operations: create and search on the
collection endpoint, and read, update, and delete on an item endpoint.

All DOI-settings operations require either an Invenio system-process identity
or an administration identity. The same policy applies to create, read, search,
update, and delete.

## Administration interface

The extension registers **DOI Configuration** under **Site management**. The
view supports searching, creating, editing, viewing, and deleting DOI settings.
It displays the community, prefix, DataCite username, and timestamps; passwords
are deliberately not displayed.

## Application customization

During extension initialization, the package handles record and parent/concept
DOI configuration independently:

- It creates each provider list only when it is absent. If that list has no
  provider named `datacite`, it appends the package's default DataCite provider.
- It adds the default `doi` identifier configuration with `setdefault`. An
  existing `RDM_PERSISTENT_IDENTIFIERS["doi"]` or
  `RDM_PARENT_PERSISTENT_IDENTIFIERS["doi"]` mapping is left unchanged.

This means that existing identifiers are preserved. For example, an application
that configures only OAI before this extension is initialized:

```python
RDM_PERSISTENT_IDENTIFIER_PROVIDERS = [oai_provider]
RDM_PERSISTENT_IDENTIFIERS = {
    "oai": {"providers": ["oai"], "required": False},
}

RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS = [parent_oai_provider]
RDM_PARENT_PERSISTENT_IDENTIFIERS = {
    "oai": {"providers": ["oai"], "required": False},
}
```

keeps its OAI configuration. The extension appends its `datacite` provider to
both provider lists and adds its default `doi` mappings. The resulting lists
contain both OAI and DataCite providers.

For the underlying InvenioRDM DOI behavior, DataCite configuration, and
`RDM_PERSISTENT_IDENTIFIERS` options, see the official
[InvenioRDM DOI registration documentation](https://inveniordm.docs.cern.ch/operate/customize/dois/).

To replace the DOI setup entirely, define a provider named `datacite` and the
corresponding `doi` mapping before the extension initializes. The extension
then leaves both definitions intact. The following example also enables the
multiple-model serializer:


## Configuration example

```python
import idutils

from invenio_i18n import lazy_gettext as _

from oarepo_doi.resources.serializers import OarepoDataciteJSONSerializer
from oarepo_doi.services.providers.client import DataCiteRecordAwareClient
from oarepo_doi.services.providers.provider import DataCiteRecordAwareProvider

RDM_PERSISTENT_IDENTIFIER_PROVIDERS = [
    DataCiteRecordAwareProvider(
        "datacite",
        client=DataCiteRecordAwareClient("datacite", config_prefix="DATACITE"),
        serializer=OarepoDataciteJSONSerializer(),
        label=_("DOI"),
    ),
]

RDM_PERSISTENT_IDENTIFIERS = {
    "doi": {
        "providers": ["datacite"],
        "required": True,
        "label": _("DOI"),
        "validator": idutils.is_doi,
        "normalizer": idutils.normalize_doi,
        "is_enabled": DataCiteRecordAwareProvider.is_enabled,
        "ui": {"default_selected": "no"},
    },
}

RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS = [
    DataCiteRecordAwareProvider(
        "datacite",
        client=DataCiteRecordAwareClient("datacite", config_prefix="DATACITE"),
        serializer=OarepoDataciteJSONSerializer(schema_context={"is_parent": True}),
        label=_("Concept DOI"),
    ),
]

RDM_PARENT_PERSISTENT_IDENTIFIERS = {
    "doi": {
        "providers": ["datacite"],
        "required": True,
        "condition": lambda rec: rec.pids.get("doi", {}).get("provider") == "datacite",
        "label": _("Concept DOI"),
        "validator": idutils.is_doi,
        "normalizer": idutils.normalize_doi,
        "is_enabled": DataCiteRecordAwareProvider.is_enabled,
    },
}
```
