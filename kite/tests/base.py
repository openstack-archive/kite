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

from oslotest import base

from kite.common import service
from kite.openstack.common.fixture import config


class BaseTestCase(base.BaseTestCase):

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.config_fixture = self.useFixture(config.Config())
        self.CONF = self.config_fixture.conf

        service.parse_args(args=[])

    def config(self, *args, **kwargs):
        self.config_fixture.config(*args, **kwargs)
