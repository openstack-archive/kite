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

from oslo.config import cfg

from kite.openstack.common.db import options
from kite.openstack.common import log

_COMMON_PATH = os.path.abspath(os.path.dirname(__file__))
_ROOT_PATH = os.path.normpath(os.path.join(_COMMON_PATH, '..', '..'))
_DEFAULT_SQL_CONNECTION = 'sqlite:///%s' % os.path.join(_ROOT_PATH,
                                                        'kite.sqlite')

CONF = cfg.CONF

API_SERVICE_OPTS = [
    cfg.StrOpt('bind_ip',
               default='0.0.0.0',
               help='IP for the server to bind to'),
    cfg.IntOpt('port',
               default=9109,
               help='The port for the server'),
    cfg.IntOpt('ticket_lifetime',
               default=3600,
               help='Length of ticket validity (in seconds)'),
]

CONF.register_opts(API_SERVICE_OPTS)


def parse_args(args, default_config_files=None):
    CONF(args=args[1:],
         project='kite',
         default_config_files=default_config_files)


def prepare_service(argv=[]):
    options.set_defaults(sql_connection=_DEFAULT_SQL_CONNECTION,
                         sqlite_db='kite.sqlite')
    cfg.set_defaults(log.log_opts,
                     default_log_levels=['sqlalchemy=WARN',
                                         'eventlet.wsgi.server=WARN'
                                         ])
    parse_args(argv)
    log.setup('kite')
