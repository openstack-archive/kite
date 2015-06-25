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

import logging
import sys
from wsgiref import simple_server

from oslo_config import cfg

from kite.api import app
from kite.common import service
from kite.openstack.common import gettextutils
from kite.openstack.common import log

PROJECT = 'kite'
gettextutils.install(PROJECT)


CONF = cfg.CONF


class Application(object):
    def __init__(self):
        self.app = app.setup_app()

    def __call__(self, environ, start_response):
        return self.app(environ, start_response)


def main():
    service.prepare_service(sys.argv)

    # Build and start the WSGI app
    host = CONF.bind_ip
    port = CONF.port
    wsgi = simple_server.make_server(host, port, Application())

    LOG = log.getLogger(__name__)
    LOG.info(_("Serving on http://%(host)s:%(port)d"), {'host': host,
                                                        'port': port})
    CONF.log_opt_values(LOG, logging.INFO)

    try:
        wsgi.serve_forever()
    except KeyboardInterrupt:
        pass
