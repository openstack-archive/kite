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

import pecan
from pecan import rest
import wsme
import wsmeext.pecan as wsme_pecan

from kite.api.v1 import models


class KeyController(rest.RestController):

    @wsme.validate(models.KeyData)
    @wsme_pecan.wsexpose(models.KeyData, wsme.types.text, body=models.KeyInput)
    def put(self, key_name, key_input):
        generation = pecan.request.storage.set_key(key_name,
                                                   key_input.key)
        return models.KeyData(name=key_name, generation=generation)
