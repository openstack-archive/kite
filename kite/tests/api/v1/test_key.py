# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import base64

from kite.common import exception
from kite.tests.api.v1 import base

DEFAULT_REQUESTOR = 'home.local'
REQUEST_KEY = base64.b64decode('LDIVKc+m4uFdrzMoxIhQOQ==')
REQUEST_KEY2 = base64.b64decode('LyyszflO/JZXLpPV0CtHdQ==')


class KeyApiTests(base.BaseTestCase):

    def test_key_setting(self):
        resp = self.put('keys/%s' % DEFAULT_REQUESTOR,
                        status=200,
                        json={'key': base64.b64encode(REQUEST_KEY)})

        key = self.DB.get_key(DEFAULT_REQUESTOR)

        self.assertNotEqual(REQUEST_KEY, key['key'])
        self.assertNotEqual(REQUEST_KEY, key['signature'])

        key_data = self.STORAGE.get_key(DEFAULT_REQUESTOR)

        self.assertEqual(REQUEST_KEY, key_data['key'])

        self.assertEqual(DEFAULT_REQUESTOR, resp.json['name'])
        self.assertEqual(key_data['generation'], resp.json['generation'])

    def test_override_key(self):
        resp1 = self.put('keys/%s' % DEFAULT_REQUESTOR,
                         status=200,
                         json={'key': base64.b64encode(REQUEST_KEY)})

        key1 = self.STORAGE.get_key(DEFAULT_REQUESTOR)

        self.assertEqual(REQUEST_KEY, key1['key'])
        self.assertEqual(resp1.json['generation'], key1['generation'])

        resp2 = self.put('keys/%s' % DEFAULT_REQUESTOR,
                         status=200,
                         json={'key': base64.b64encode(REQUEST_KEY2)})

        key2 = self.STORAGE.get_key(DEFAULT_REQUESTOR)

        self.assertEqual(REQUEST_KEY2, key2['key'])
        self.assertEqual(resp2.json['generation'], key2['generation'])

    def test_delete_key(self):
        self.put('keys/%s' % DEFAULT_REQUESTOR,
                 status=200,
                 json={'key': base64.b64encode(REQUEST_KEY)})

        key1 = self.STORAGE.get_key(DEFAULT_REQUESTOR)
        self.assertEqual(REQUEST_KEY, key1['key'])

        self.delete('keys/%s' % DEFAULT_REQUESTOR, status=204)

        ok = False
        try:
            self.STORAGE.get_key(DEFAULT_REQUESTOR)
        except exception.KeyNotFound:
            ok = True

        self.assertEqual(True, ok)
