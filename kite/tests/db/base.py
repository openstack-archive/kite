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

from sqlalchemy import exc

from kite.db.kvs import api as kvs_api
from kite.db.sqlalchemy import api as sql_api
from kite.openstack.common.db.sqlalchemy import migration
from kite.openstack.common.db.sqlalchemy import test_base
from kite.openstack.common.fixture import lockutils
from kite.tests import base
from kite.tests import paths

postgres_fixture = test_base.PostgreSQLOpportunisticFixture
mysql_fixture = test_base.MySQLOpportunisticFixture


class BaseTestCase(base.BaseTestCase):

    sql_scenarios = [('sqlitedb', {'sql_fixture': test_base.DbFixture,
                                   'backend': sql_api.SqlalchemyDbImpl,
                                   'opportunistic': False}),
                     ('postgres', {'sql_fixture': postgres_fixture,
                                   'backend': sql_api.SqlalchemyDbImpl,
                                   'opportunistic': True}),
                     ('mysql', {'sql_fixture': mysql_fixture,
                                'backend': sql_api.SqlalchemyDbImpl,
                                'opportunistic': True})]

    kvs_scenarios = [('kvsdb', {'sql_fixture': None,
                                'backend': kvs_api.KvsDbImpl})]

    scenarios = sql_scenarios + kvs_scenarios

    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.sessionmaker = None

        if self.sql_fixture:
            if self.opportunistic:
                driver = self.sql_fixture.DRIVER
                self.useFixture(lockutils.LockFixture('test-%s' % driver))

            try:
                self.useFixture(self.sql_fixture(self))
            except exc.OperationalError:
                if self.opportunistic:
                    self.skipTest('Opportunistic Backend not supported')
                else:
                    raise
            else:
                repo_path = paths.root_path('db', 'sqlalchemy', 'migrate_repo')
                migration.db_sync(self.engine, repo_path)
                self.addCleanup(migration.db_sync, self.engine, repo_path, 0)

        self.DB = self.backend(self.sessionmaker)
