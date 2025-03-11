# OARepo DOI

### Configuration example

```
DATACITE_URL = 'https://api.test.datacite.org/dois'

DATACITE_MAPPING = {'local://documents-1.0.0.json':"common.mapping.DataCiteMappingNRDocs"}

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
    
### Mapping example

```python
class DataCiteMappingNRDocs:

    def metadata_check(self, data, errors=[]):
        
        data = data["metadata"]
        if "title" not in data:
            errors.append("Title is mandatory")
        
        return errors

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
