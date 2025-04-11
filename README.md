# OARepo DOI

### Configuration example

```
DATACITE_URL = 'https://api.test.datacite.org/dois'

DATACITE_MODE = "AUTOMATIC_DRAFT"

DATACITE_CREDENTIALS = {"generic": {"prefix": "10.23644" , "password": "yyyy", "username": "xxx"}}

DATACITE_CREDENTIALS_DEFAULT = {"prefix": "10.23644" , "password": "yyy", "username": "xxxx"}

DATACITE_SPECIFIED_ID = True
```

mode types:
  - `AUTOMATIC_DRAFT` - dois will be assigned automatically when draft is creadet
  - `AUTOMATIC` - dois will be assigned automatically after publish 
  - `ON_EVENT` - dois are assigned after request

DATACITE_SPECIFIED_ID
  - Default value - False
  - If true, the doi suffix will be the same as record pid
    
### Providers
The DOI request is made through providers. To implement a new provider, you need to create a custom class that inherits from the `OarepoDataCitePIDProvider` from the `oarepo_doi.services.provider` module. This custom provider class should include your own metadata mapping.

Example of custom provider implementation:
```python
from oarepo_doi.services.provider import OarepoDataCitePIDProvider

class NRDocsDataCitePIDProvider(OarepoDataCitePIDProvider):

    def metadata_check(self, record):
        
        data = record["metadata"]
        if "title" not in data:
            record.append("Title is mandatory")
        
        return record

    def create_datacite_payload(self, data):
        titles = {"title": "xy"}

        
        payload = {
            "data": {
                "type": "dois",
                "attributes": {
                }
            }
        }
        payload["data"]["attributes"]["titles"] = titles
   
        return payload
    
```
Next, the provider must be added to the Invenio configuration (invenio.cfg). For DOI client communication, the `DataCiteClient` from `invenio_rdm_records.services.pids.providers` is used.

Example of the configuration:
```
RDM_PERSISTENT_IDENTIFIER_PROVIDERS = [
    # DataCite Concept DOI provider
    NRDocsDataCitePIDProvider(
        "datacite",
        client=DataCiteClient("datacite", config_prefix="DATACITE"),
        label=_("DOI"),
    ),
]
RDM_PERSISTENT_IDENTIFIERS = {
    "doi": {
        "providers": ["datacite"],
        "label": _("DOI"),
        "is_enabled": NRDocsDataCitePIDProvider.is_enabled,
    },
    }
RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS = [
    # DataCite Concept DOI provider
    NRDocsDataCitePIDProvider(
        "datacite",
        client=DataCiteClient("datacite", config_prefix="DATACITE"),
        label=_("DOI"),
    ),
]

RDM_PARENT_PERSISTENT_IDENTIFIERS = {
    "doi": {
        "providers": ["datacite"],
        "label": _("DOI"),
        "is_enabled": NRDocsDataCitePIDProvider.is_enabled,
    },
}
```