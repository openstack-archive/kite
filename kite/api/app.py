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

from oslo_config import cfg
import oslo_middleware.cors as cors_middleware
import pecan

from kite.api import hooks
from kite.api import root

CONF = cfg.CONF

DEFAULT_CONFIG = {'app': {}}


def setup_app(config=None):
    app_hooks = [hooks.ConfigHook(),
                 hooks.CryptoHook(),
                 hooks.StorageHook(),
                 ]

    app = pecan.make_app(root.RootController(),
                         debug=CONF.debug,
                         hooks=app_hooks)

    # Create a CORS wrapper, and attach kite-specific defaults that must be
    # included in all CORS responses. This should be the last middleware in
    # this method (resulting in it being the first middleware in the chain),
    # in order to ensure that it can annotate any error responses from other
    # components and/or middleware in the application.
    app = cors_middleware.CORS(app, CONF)
    app.set_latent(
        allow_methods=['GET', 'PUT', 'POST', 'DELETE'],
    )

    return app
