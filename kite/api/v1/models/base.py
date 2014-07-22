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
import functools

import pecan
import wsme

from kite.common import exception
from kite.common import utils
from kite.openstack.common import jsonutils
from kite.openstack.common import timeutils


def memoize(f):
    """Create a property and cache the return value for future."""
    @property
    @functools.wraps(f)
    def wrapper(self):
        try:
            val = self._cache[f.func_name]
        except KeyError:
            val = f(self)
            self._cache[f.func_name] = val

        return val

    return wrapper


def malformed(msg):
    """Raise a malformed message exception if something goes wrong."""
    def wrap(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception:
                pecan.abort(400, 'Invalid %s' % msg)

        return wrapper
    return wrap


class Endpoint(object):
    """A source or destination for a ticket."""

    def __init__(self, endpoint_str, group=None):
        self._cache = dict()
        self._set_endpoint(endpoint_str)
        self._group = group

    @malformed('endpoint')
    def _set_endpoint(self, endpoint_str):
        self.host, self.generation = utils.split_host(endpoint_str)

    @memoize
    def key_data(self):
        try:
            return pecan.request.storage.get_key(self.host,
                                                 self.generation,
                                                 group=self._group)
        except exception.CryptoError:
            pecan.abort(500, "Failed to decrypt key for '%s:%s'. " %
                        (self.host, self.generation))
        except exception.KeyNotFound:
            pecan.abort(404, "Could not find key")

    @property
    def key(self):
        return self.key_data['key']

    @property
    def key_group(self):
        return self.key_data['group']

    @property
    def key_generation(self):
        return self.key_data['generation']

    @property
    def key_str(self):
        return utils.join_host(self.host, self.key_generation)


class BaseRequest(wsme.types.Base):

    metadata = wsme.wsattr(wsme.types.text, mandatory=True)
    signature = wsme.wsattr(wsme.types.text, mandatory=True)

    def __init__(self, **kwargs):
        super(BaseRequest, self).__init__(**kwargs)
        self._cache = dict()
        self.now = timeutils.utcnow()

        # NOTE(jamielennox): This is essentially a class variable, however
        # that confuses WSME.
        self.destination_is_group = None

    @memoize
    @malformed("metadata")
    def meta(self):
        return jsonutils.loads(base64.decodestring(self.metadata))

    @memoize
    @malformed("source")
    def source(self):
        return Endpoint(self.meta['source'], group=False)

    @memoize
    @malformed("destination")
    def destination(self):
        return Endpoint(self.meta['destination'],
                        group=self.destination_is_group)

    @memoize
    @malformed("timestamp")
    def timestamp(self):
        return timeutils.parse_strtime(self.meta['timestamp'])

    @property
    @malformed("nonce")
    def nonce(self):
        return self.meta['nonce']

    @property
    def time_str(self):
        return timeutils.strtime(self.now)

    def verify(self):
        """Ensure that the ticket request is recent enough to be valid and
        the signature is correct for the requestor.
        """
        if (self.now - self.timestamp) > self.ttl:
            pecan.abort(401, 'Ticket validity expired')

        if not self.nonce:
            # just check this until we actually use it
            pecan.abort(400, 'Invalid nonce')

        try:
            sigc = pecan.request.crypto.sign(self.source.key, self.metadata)
        except exception.CryptoError:
            pecan.abort(400, "Unexpected error: Couldn't reproduce signature")

        if sigc != self.signature:
            pecan.abort(401, 'Invalid Signature')


class BaseResponse(wsme.types.Base):

    metadata = wsme.wsattr(wsme.types.text, mandatory=True)
    signature = wsme.wsattr(wsme.types.text, mandatory=True)

    def set_metadata(self, source, destination, expiration):
        """Attach the generation metadata to the ticket.

        This informs the client and server of expiration and the expect sending
        and receiving host and will be validated by both client and server.
        """
        metadata = jsonutils.dumps({'source': source,
                                    'destination': destination,
                                    'expiration': expiration,
                                    'encryption': True})
        self.metadata = base64.b64encode(metadata)

    def sign(self, key, data):
        """Sign the response.

        This will be signed with the requestor's key so that it knows that the
        issuing server has a correct copy of the key.
        """
        self.signature = pecan.request.crypto.sign(key, self.metadata + data)
