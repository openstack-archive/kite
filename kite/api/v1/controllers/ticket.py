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

import pecan
from pecan import rest
import wsme
import wsmeext.pecan as wsme_pecan

from kite.api.v1 import models
from kite.openstack.common import jsonutils


class TicketController(rest.RestController):

    @wsme.validate(models.Ticket)
    @wsme_pecan.wsexpose(models.Ticket, body=models.TicketRequest)
    def post(self, ticket_request):
        # verify all required fields present and the signature is correct
        ticket_request.verify()

        # create a new random base key. With the combination of this base key
        # and the information available in the metadata a client will be able
        # to re-generate the keys required for this session.
        rndkey = pecan.request.crypto.extract(ticket_request.source.key,
                                              pecan.request.crypto.new_key())

        # generate the keys to communicate between these two endpoints.
        e_key, s_key = pecan.request.crypto.generate_keys(rndkey,
                                                          ticket_request.info)

        # encrypt the base key for the target, this can be used to generate
        # the sek on the target
        esek_data = {'key': base64.b64encode(rndkey),
                     'timestamp': ticket_request.time_str,
                     'ttl': ticket_request.ttl.seconds}

        # encrypt returns a base64 encrypted string
        esek = pecan.request.crypto.encrypt(ticket_request.destination.key,
                                            jsonutils.dumps(esek_data))

        return ticket_request.new_response(e_key, s_key, esek)
