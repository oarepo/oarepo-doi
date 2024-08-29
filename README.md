# OARepo DOI

### configuration example

DATACITE_URL = 'https://api.test.datacite.org/dois'

DATACITE_MAPPING = {'local://documents-1.0.0.json':"common.mapping.DataCiteMappingNRDocs"}

DATACITE_MODE = "AUTOMATIC_DRAFT"

DATACITE_CREDENTIALS = {"generric": {"mode": "AUTOMATIC_DRAFT", "prefix": "10.23644" , "password": "yyyy", "username": "xxx"}}

DATACITE_CREDENTIALS_DEFAULT = {"mode": "AUTOMATIC_DRAFT", "prefix": "10.23644" , "password": "yyy", "username": "xxxx"}


mode types:
  - AUTOMATIC_DRAFT - dois will be assigned automatically when draft is creadet
  - AUTOMATIC - dois will be assigned automatically after publish 
  - ON_EVENT - dois are assigned after request

