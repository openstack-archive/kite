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
import datetime

from kite.common import crypto
from kite.common import exception
from kite.common import storage
from kite.tests.unit import base

from oslo_utils import timeutils

TEST_KEY = 'test-key'
TEST_NAME = 'test-name'


class StorageTests(base.BaseTestCase):

    def setUp(self):
        super(StorageTests, self).setUp()
        self.CRYPTO = crypto.CryptoManager.get_instance()
        self.STORAGE = storage.StorageManager.get_instance()

    def test_get_set(self):
        gen = self.STORAGE.set_key(TEST_NAME, TEST_KEY)

        key_data = self.STORAGE.get_key(TEST_NAME)
        self.assertEqual(key_data['key'], TEST_KEY)
        self.assertEqual(key_data['name'], TEST_NAME)
        self.assertEqual(key_data['generation'], gen)
        self.assertEqual(key_data['group'], False)

    def test_expired(self):
        past = timeutils.utcnow() - datetime.timedelta(minutes=10)
        self.STORAGE.set_key(TEST_NAME, TEST_KEY, past)
        self.assertRaises(exception.KeyNotFound,
                          self.STORAGE.get_key, TEST_NAME)

    def test_retrieve_fails_without_mkey(self):
        self.STORAGE.set_key(TEST_NAME, TEST_KEY)
        self.CRYPTO.mkey = None

        self.assertRaises(exception.CryptoError,
                          self.STORAGE.get_key, TEST_NAME)

    def test_store_fails_without_mkey(self):
        self.CRYPTO.mkey = None

        self.assertRaises(exception.CryptoError,
                          self.STORAGE.set_key, TEST_NAME, TEST_KEY)

    def test_storage_key_failure(self):
        self.STORAGE.set_key(TEST_NAME, TEST_KEY)
        self.CRYPTO.mkey = base64.b64decode('Jx5CVBcxuA86050355mTrg==')
        self.assertRaises(exception.CryptoError,
                          self.STORAGE.get_key, TEST_NAME)

    def test_overwrite_key(self):
        another_key = 'another-key'
        self.STORAGE.set_key(TEST_NAME, TEST_KEY)
        self.assertEqual(self.STORAGE.get_key(TEST_NAME)['key'], TEST_KEY)
        self.STORAGE.set_key(TEST_NAME, another_key)
        self.assertEqual(self.STORAGE.get_key(TEST_NAME)['key'], another_key)

    def test_raises_for_unset_key(self):
        self.assertRaises(exception.KeyNotFound,
                          self.STORAGE.get_key, TEST_NAME)
