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

import six

from kite.openstack.common.crypto import utils as cryptoutils
from kite.tests.api.v1 import base

from oslo_serialization import jsonutils
from oslo_utils import timeutils

SOURCE_KEY = base64.b64decode('LDIVKc+m4uFdrzMoxIhQOQ==')
DEST_KEY = base64.b64decode('EEGfTxGFcZiT7oPO+brs+A==')

TEST_KEY = base64.b64decode('Jx5CVBcxuA86050355mTrg==')

DEFAULT_SOURCE = 'home.local'
DEFAULT_DEST = 'tests.openstack.remote'
DEFAULT_GROUP = 'home'
DEFAULT_NONCE = '42'


class TicketTest(base.BaseTestCase):

    def setUp(self):
        super(TicketTest, self).setUp()

        self.crypto = cryptoutils.SymmetricCrypto(
            enctype=self.CONF.crypto.enctype,
            hashtype=self.CONF.crypto.hashtype)

    def _ticket_metadata(self, source=DEFAULT_SOURCE,
                         destination=DEFAULT_DEST, nonce=DEFAULT_NONCE,
                         timestamp=None, b64encode=True):
        if not timestamp:
            timestamp = timeutils.utcnow()

        return {'source': source, 'destination': destination,
                'nonce': nonce, 'timestamp': timestamp}

    def _add_key(self, name, key=None, b64encode=True):
        if not key:
            if name == DEFAULT_SOURCE:
                key = SOURCE_KEY
            elif name == DEFAULT_DEST:
                key = DEST_KEY
            else:
                raise ValueError("No default key available")

        if b64encode:
            key = base64.b64encode(key)

        resp = self.put('keys/%s' % name,
                        status=200,
                        json={'key': key}).json

        return "%s:%s" % (resp['name'], resp['generation'])

    def _request_ticket(self, metadata=None, signature=None,
                        source=DEFAULT_SOURCE, destination=DEFAULT_DEST,
                        nonce=DEFAULT_NONCE, timestamp=None,
                        source_key=None, status=200):
        if not metadata:
            metadata = self._ticket_metadata(source=source,
                                             nonce=nonce,
                                             destination=destination,
                                             timestamp=timestamp)

        if not isinstance(metadata, six.text_type):
            metadata = base64.b64encode(jsonutils.dumps(metadata))

        if not signature:
            if not source_key and source == DEFAULT_SOURCE:
                source_key = SOURCE_KEY

            signature = self.crypto.sign(source_key, metadata)

        return self.post('tickets',
                         json={'metadata': metadata, 'signature': signature},
                         status=status)

    def test_valid_ticket(self):
        self._add_key(DEFAULT_SOURCE)
        self._add_key(DEFAULT_DEST)

        response = self._request_ticket().json

        b64m = response['metadata']
        metadata = jsonutils.loads(base64.b64decode(b64m))
        signature = response['signature']
        b64t = response['ticket']

        # check signature was signed to source
        csig = self.crypto.sign(SOURCE_KEY, b64m + b64t)
        self.assertEqual(signature, csig)

        # decrypt the ticket base if required, done by source
        if metadata['encryption']:
            ticket = self.crypto.decrypt(SOURCE_KEY, b64t)

        ticket = jsonutils.loads(ticket)

        skey = base64.b64decode(ticket['skey'])
        ekey = base64.b64decode(ticket['ekey'])
        b64esek = ticket['esek']

        # the esek part is sent to the destination, so destination should be
        # able to decrypt it from here.
        esek = self.crypto.decrypt(DEST_KEY, b64esek)
        esek = jsonutils.loads(esek)

        self.assertEqual(int(self.CONF.ticket_lifetime), esek['ttl'])

        # now should be able to reconstruct skey, ekey from esek data
        info = '%s,%s,%s' % (metadata['source'], metadata['destination'],
                             esek['timestamp'])

        key = base64.b64decode(esek['key'])
        new_sig, new_key = self.CRYPTO.generate_keys(key, info)

        self.assertEqual(new_key, ekey)
        self.assertEqual(new_sig, skey)

    def test_missing_source_key(self):
        self._add_key(DEFAULT_DEST)
        self._request_ticket(status=404)

    def test_missing_dest_key(self):
        self._add_key(DEFAULT_SOURCE)
        self._request_ticket(status=404)

    def test_wrong_source_key(self):
        # install TEST_KEY but sign with SOURCE_KEY
        self._add_key(DEFAULT_SOURCE, TEST_KEY)
        self._add_key(DEFAULT_DEST)

        self._request_ticket(status=401)

    def test_invalid_signature(self):
        self._add_key(DEFAULT_SOURCE)
        self._add_key(DEFAULT_DEST)

        self._request_ticket(status=401, signature='bad-signature')

    def test_invalid_expired_request(self):
        self._add_key(DEFAULT_SOURCE)
        self._add_key(DEFAULT_DEST)

        timestamp = timeutils.utcnow() - datetime.timedelta(hours=5)

        self._request_ticket(status=401, timestamp=timestamp)

    def test_fails_on_garbage_metadata(self):
        self._request_ticket(metadata='garbage',
                             signature='signature',
                             status=400)

        self._request_ticket(metadata='{"json": "string"}',
                             signature='signature',
                             status=400)

    def test_missing_attributes_in_metadata(self):
        self._add_key(DEFAULT_SOURCE)
        self._add_key(DEFAULT_DEST)

        for attr in ['source', 'timestamp', 'destination', 'nonce']:
            metadata = self._ticket_metadata(b64encode=False)
            del metadata[attr]

            self._request_ticket(metadata=metadata, status=400)
