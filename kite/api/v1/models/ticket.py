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

import pecan
import wsme

from kite.api.v1.models import base

from oslo_serialization import jsonutils


class Ticket(base.BaseResponse):

    ticket = wsme.wsattr(wsme.types.text, mandatory=True)

    def set_ticket(self, rkey, enc_key, signature, esek):
        """Create and encrypt a ticket to the requestor.

        The requestor will be able to decrypt the ticket with their key and the
        information in the metadata to get the new point-to-point key.
        """
        ticket = jsonutils.dumps({'skey': base64.b64encode(signature),
                                  'ekey': base64.b64encode(enc_key),
                                  'esek': esek})

        self.ticket = pecan.request.crypto.encrypt(rkey, ticket)

    def sign(self, key):
        """Sign the ticket response.

        This will be signed with the requestor's key so that it knows that the
        issuing server has a correct copy of the key.
        """
        super(Ticket, self).sign(key, self.ticket)


class TicketRequest(base.BaseRequest):

    def __init__(self, **kwargs):
        super(TicketRequest, self).__init__(**kwargs)

        seconds = int(pecan.request.conf.ticket_lifetime)
        self.ttl = datetime.timedelta(seconds=seconds)

    @property
    def info(self):
        """A predictable text string that can be used as the base for
        generating keys.
        """
        return "%s,%s,%s" % (self.source.key_str,
                             self.destination.key_str,
                             self.time_str)

    def new_response(self, enc_key, signature, esek):
        response = Ticket()

        response.set_metadata(source=self.source.key_str,
                              destination=self.destination.key_str,
                              expiration=self.now + self.ttl)

        # encrypt the sig and key back to the requester as well as the esek
        # to forward with messages.
        response.set_ticket(self.source.key, enc_key, signature, esek)

        # finish building response and sign it, we sign it with the requester's
        # key at the end because the ticket doesn't have to be encrypted and we
        # still have to provide integrity of the ticket.
        response.sign(self.source.key)

        return response
