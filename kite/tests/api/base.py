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

import pecan.testing
import webtest

from kite.common import crypto
from kite.common import storage
from kite.db import api as db_api
from kite.openstack.common import jsonutils
from kite.tests import base


def urljoin(*args):
    return "/%s" % "/".join([a.strip("/") for a in args])


def method_func(method):
    def func(self, url, **kwargs):
        kwargs['method'] = method
        return self.request(url, **kwargs)

    return func


class BaseTestCase(base.BaseTestCase):

    METHODS = {'get': webtest.TestApp.get,
               'post': webtest.TestApp.post,
               'put': webtest.TestApp.put,
               'patch': webtest.TestApp.patch,
               'delete': webtest.TestApp.delete,
               'options': webtest.TestApp.options,
               'head': webtest.TestApp.head}

    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.config_fixture.config(backend='kvs', group='database')
        db_api.reset()

        root = 'kite.api.root.RootController'
        self.app_config = {
            'app': {
                'root': root,
                'modules': ['kite.api'],
            },
        }

        self.CRYPTO = crypto.CryptoManager.get_instance()
        self.DB = db_api.get_instance()
        self.STORAGE = storage.StorageManager.get_instance()

        self.app = pecan.testing.load_test_app(self.app_config)
        self.addCleanup(pecan.set_config, {}, overwrite=True)

    def request(self, url, method, **kwargs):
        try:
            json = kwargs.pop('json')
        except KeyError:
            pass
        else:
            kwargs['content_type'] = 'application/json'
            kwargs['params'] = jsonutils.dumps(json)

        try:
            func = self.METHODS[method.lower()]
        except KeyError:
            self.fail("Unsupported HTTP Method: %s" % method)
        else:
            return func(self.app, url, **kwargs)

    get = method_func('get')
    post = method_func('post')
    put = method_func('put')
    delete = method_func('delete')
    options = method_func('options')
    head = method_func('head')
