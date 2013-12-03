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

import os

from kite.db.kvs import api as kvs_api
from kite.db.sqlalchemy import api as sql_api
from kite.db.sqlalchemy import migration
from kite.tests import base

connection = os.getenv('OS_TEST_DBAPI_CONNECTION', 'sqlite:///test.db')

# TODO(jamielennox): there is some support in OSLO for migration tests and
# opportunistic tests. We should do more extensive real testing.


class BaseTestCase(base.BaseTestCase):

    scenarios = [('sqlitedb', {'connection': connection,
                               'backend': sql_api}),
                 ('kvsdb', {'connection': None,
                            'backend': kvs_api})
                 ]

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.backend.reset()

        if self.connection:
            self.config_fixture.config(connection=self.connection,
                                       group='database')
            migration.upgrade()
            self.addCleanup(migration.downgrade)

        self.DB = self.backend.get_backend()
