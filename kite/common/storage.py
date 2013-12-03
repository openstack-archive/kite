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

from kite.common import crypto
from kite.common import exception
from kite.common import utils
from kite.db import api as dbapi
from kite.openstack.common import timeutils


class StorageManager(utils.SingletonManager):

    def get_key(self, name, generation=None, group=None):
        """Retrieves a key from the driver and decrypts it for use.

        :param string name: Key Identifier
        :param int generation: Key generation to retrieve. Default latest

        :return tuple (string, int): raw key data and the key generation
        """
        key = dbapi.get_instance().get_key(name, generation=generation,
                                           group=group)

        if not key:
            raise exception.KeyNotFound(name=name, generation=generation)

        expiration = key.get('expiration')
        if expiration:
            now = timeutils.utcnow()
            if expiration < now:
                raise exception.KeyNotFound(name=name, generation=generation)

        crypto_manager = crypto.CryptoManager.get_instance()
        return {'key': crypto_manager.decrypt_key(name,
                                                  enc_key=key['key'],
                                                  signature=key['signature']),
                'generation': key['generation'],
                'name': key['name'],
                'group': key['group']}

    def set_key(self, name, key, expiration=None):
        """Encrypt a key and store it to the backend.

        :param string key_id: Key Identifier
        :param string keyblock: raw key data
        """
        crypto_manager = crypto.CryptoManager.get_instance()
        enc_key, signature = crypto_manager.encrypt_key(name, key)
        return dbapi.get_instance().set_key(name, key=enc_key,
                                            signature=signature,
                                            group=False, expiration=expiration)
