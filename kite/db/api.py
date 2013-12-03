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

from oslo.config import cfg

from kite.openstack.common.db import api as db_api

CONF = cfg.CONF
IMPL = None

CONF.import_opt('backend',
                'kite.openstack.common.db.options',
                group='database')

_BACKEND_MAPPING = {'sqlalchemy': 'kite.db.sqlalchemy.api',
                    'kvs': 'kite.db.kvs.api'}


def reset():
    global IMPL
    IMPL = None


def get_instance(force_new=False):
    """Return a DB API instance."""
    global IMPL
    if not IMPL or force_new:
        IMPL = db_api.DBAPI(CONF.database.backend,
                            backend_mapping=_BACKEND_MAPPING)

    return IMPL
