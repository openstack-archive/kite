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

import datetime

from kite.common import crypto
from kite.common import exception
from kite.common import utils
from kite.db import api as dbapi
from kite.openstack.common import timeutils


class StorageManager(utils.SingletonManager):

    def get_key(self, name, generation=None, group=None):
        """Retrieves a key from the driver and decrypts it for use.

        If it is a group key and it has expired or is not found then generate
        a new one and return that for use.

        :param string name: Key Identifier
        :param int generation: Key generation to retrieve. Default latest
        """
        key = dbapi.get_instance().get_key(name, generation=generation,
                                           group=group)
        crypto_manager = crypto.CryptoManager.get_instance()

        if not key:
            # host or group not found
            raise exception.KeyNotFound(name=name, generation=generation)

        if group is not None and group != key['group']:
            raise exception.KeyNotFound(name=name, generation=generation)

        now = timeutils.utcnow()
        expiration = key.get('expiration')

        if key['group'] and expiration and generation is not None:
            # if you ask for a specific group key generation then you can
            # retrieve it for a little while beyond it being expired
            timeout = expiration + datetime.timedelta(minutes=10)
        elif key['group'] and expiration:
            # when we can generate a new key we don't want to use an older one
            # that is just going to require refreshing soon
            timeout = expiration - datetime.timedelta(minutes=2)
        else:
            # otherwise we either have an un-expiring group or host key which
            # we just check against now
            timeout = now

        if expiration and expiration <= timeout:
            if key['group']:
                # clear the key so it will generate a new group key
                key = {'group': True}
            else:
                raise exception.KeyNotFound(name=name, generation=generation)

        if 'key' in key:
            dec_key = crypto_manager.decrypt_key(name,
                                                 enc_key=key['key'],
                                                 signature=key['signature'])
            return {'key': dec_key,
                    'generation': key['generation'],
                    'name': key['name'],
                    'group': key['group']}

        if generation is not None or not key['group']:
            # A specific generation was asked for or it's not a group key
            # so don't generate a new one
            raise exception.KeyNotFound(name=name, generation=generation)

        # generate and return a new group key
        new_key = crypto_manager.new_key()
        enc_key, signature = crypto_manager.encrypt_key(name, new_key)
        expiration = now + datetime.timedelta(minutes=15)

        new_gen = dbapi.get_instance().set_key(name,
                                               enc_key=enc_key,
                                               signature=signature,
                                               group=True,
                                               expiration=expiration)

        return {'key': new_key,
                'generation': new_gen,
                'name': name,
                'group': True,
                'expiration': expiration}

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

    def del_key(self, name):
        """Delete a key from the backend.

        :param string name: Key Identifier
        """
        dbapi.get_instance().delete_host(name, group=False)

    def create_group(self, name):
        dbapi.get_instance().create_group(name)

    def delete_group(self, name):
        dbapi.get_instance().delete_host(name, group=True)
