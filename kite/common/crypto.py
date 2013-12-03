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
import errno
import os

from oslo.config import cfg

from kite.common import exception
from kite.common import utils
from kite.openstack.common.crypto import utils as cryptoutils

CONF = cfg.CONF

CRYPTO_OPTS = [
    cfg.StrOpt('master_key_file',
               default='/etc/kite/kds.mkey',
               help='The location of the KDS master key. MUST be private. '
                    'If missing or unavailable one will be created.'),
    cfg.StrOpt('enctype',
               default='AES',
               help='Encryption Algorithm used to encrypt service keys '
                    'for storing in the database.'),
    cfg.StrOpt('hashtype',
               default='SHA256',
               help='Hashing Algorithm used when generating signatures '
                    'for integrity when storing keys to the database'),
]

CONF.register_group(cfg.OptGroup(name='crypto',
                                 title='Cryptographic Options'))
CONF.register_opts(CRYPTO_OPTS, group='crypto')


class CryptoManager(utils.SingletonManager):

    KEY_SIZE = 16

    def __init__(self):
        self.crypto = cryptoutils.SymmetricCrypto(
            enctype=CONF.crypto.enctype,
            hashtype=CONF.crypto.hashtype)
        self.hkdf = cryptoutils.HKDF(hashtype=CONF.crypto.hashtype)
        self.mkey = self._load_master_key()

    def _load_master_key(self):
        """Load the master key from file, or create one if not available."""

        # TODO(jamielennox): This is but one way that a key file could be
        # stored. This can be pluggable later for storing/fetching keys from
        # better locations.

        mkey = None

        try:
            with open(CONF.crypto.master_key_file, 'r') as f:
                mkey = base64.b64decode(f.read())
        except IOError as e:
            if e.errno == errno.ENOENT:
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
                mkey = self.crypto.new_key(self.KEY_SIZE)
                f = None
                try:
                    f = os.open(CONF.crypto.master_key_file, flags, 0o600)
                    os.write(f, base64.b64encode(mkey))
                except IOError:
                    raise e
                finally:
                    if f:
                        os.close(f)
            else:
                # the file could be unreadable due to bad permissions
                # so just pop up whatever error comes
                raise

        return mkey

    def generate_keys(self, prk, info, key_size):
        """Generate a new key from an existing key and information.

        :param string prk: Existing pseudo-random key
        :param string info: Additional information for building a new key

        :returns tuple(string, string): raw signature key, raw encryption key
        """
        key = self.hkdf.expand(prk, info, 2 * key_size)
        return key[:key_size], key[key_size:]

    def get_storage_keys(self, name):
        """Get a set of keys that will be used to encrypt the data for this
        identity in the database.

        :param string key_id: Key Identifier

        :returns tuple(string, string): raw signature key, raw encryption key
        """
        if not self.mkey:
            raise exception.CryptoError(reason=_('Failed to find mkey'))

        return self.generate_keys(self.mkey, name, self.KEY_SIZE)

    def encrypt_key(self, name, key):
        """Encrypt a key for storage.

        Returns the signature and the encryption key.
        """
        ekey, skey = self.get_storage_keys(name)

        try:
            enc_key = self.crypto.encrypt(ekey, key, b64encode=False)
            signature = self.crypto.sign(skey, enc_key, b64encode=False)
        except cryptoutils.CryptoutilsException:
            raise exception.CryptoError(reason=_('Failed to encrypt key'))

        return enc_key, signature

    def decrypt_key(self, name, enc_key, signature):
        """Decrypt a key from storage.

        Returns the raw key data.
        """
        ekey, skey = self.get_storage_keys(name)

        try:
            sigc = self.crypto.sign(skey, enc_key, b64encode=False)

            if sigc != signature:
                raise exception.CryptoError(reason=_('Signature check failed'))

            plain = self.crypto.decrypt(ekey, enc_key, b64decode=False)

        except cryptoutils.CryptoutilsException:
            raise exception.CryptoError(reason=_('Failed to decrypt key'))

        return plain
