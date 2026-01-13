#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-doi (see http://github.com/oarepo/oarepo-doi).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Test module."""

from __future__ import annotations

# doc = self.serializer.dump_obj(record)
#             doc = {"types": {
#                 "resourceTypeGeneral":"Dataset"
#             },
#                 "creators": [
#                     {
#                     "name": "P, B",
#                     "nameType": "Personal",
#                     "affiliation": [],
#                     "nameIdentifiers": []
#                     }
#                 ],"publicationYear": 2025,
#                 'identifiers': [{'identifier': '10.23644/pvqz8-1wy73', 'identifierType': 'doi'}],
#                 'publisher': 'cesnet',
#              'schemaVersion': 'http://datacite.org/schema/kernel-4',
#                 'titles': [{'title': 'qqqq'}]}
#             url = kwargs["url"]
#             self.client.for_record(record).api.public_doi(metadata=doc, url=url, doi=pid.pid_value)
