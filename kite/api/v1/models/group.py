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

import pecan
import wsme

from kite.api.v1.models import base
from kite.common import exception


class Group(wsme.types.Base):
    name = wsme.wsattr(wsme.types.text, mandatory=True)


class GroupKey(base.BaseResponse):

    group_key = wsme.wsattr(wsme.types.text, mandatory=True)

    def sign(self, key):
        super(GroupKey, self).sign(key, self.group_key)

    def set_group_key(self, rkey, group_key):
        self.group_key = pecan.request.crypto.encrypt(rkey, group_key)


class GroupKeyRequest(base.BaseRequest):

    def __init__(self, **kwargs):
        super(GroupKeyRequest, self).__init__(**kwargs)

        seconds = int(pecan.request.conf.ticket_lifetime)
        self.ttl = datetime.timedelta(seconds=seconds)
        self.destination_is_group = True

    def new_response(self):
        response = GroupKey()

        response.set_metadata(source=self.source.key_str,
                              destination=self.destination.key_str,
                              expiration=self.now + self.ttl)

        response.set_group_key(self.source.key, self.destination.key)
        response.sign(self.source.key)

        return response

    def verify(self):
        super(GroupKeyRequest, self).verify()

        # check that we are a group member
        if self.source.host.split('.')[0] != self.destination.host:
            pecan.abort(401, 'Not a group member')

        # we can only request a group key for a group
        if not self.destination.key_group:
            raise exception.KeyNotFound(name=self.destination.host,
                                        generation=self.destination.generation)
