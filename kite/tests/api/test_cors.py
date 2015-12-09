# -*- encoding: utf-8 -*-
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
Tests to assert that various incorporated middleware works as expected.
"""

from oslo_config import cfg
import oslo_middleware.cors as cors_middleware

from kite.tests.api import base


class TestCORSMiddleware(base.BaseTestCase):
    '''Provide a basic smoke test to ensure CORS middleware is active.

    The tests below provide minimal confirmation that the CORS middleware
    is active, and may be configured. For comprehensive tests, please consult
    the test suite in oslo_middleware.
    '''

    def setUp(self):
        # Make sure the CORS options are registered
        cfg.CONF.register_opts(cors_middleware.CORS_OPTS, 'cors')

        # Load up our valid domain values before the application is created.
        cfg.CONF.set_override("allowed_origin",
                              "http://valid.example.com",
                              group='cors')

        # Create the application.
        super(TestCORSMiddleware, self).setUp()

    def test_valid_cors_options_request(self):
        response = self.options('/v1/',
                                headers={
                                    'Origin': 'http://valid.example.com',
                                    'Access-Control-Request-Method': 'GET'
                                })

        # Assert response status_code.
        self.assertEqual(response.status_code, 200)
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertEqual('http://valid.example.com',
                         response.headers['Access-Control-Allow-Origin'])

    def test_invalid_cors_options_request(self):
        response = self.options('/v1/',
                                headers={
                                    'Origin': 'http://invalid.example.com',
                                    'Access-Control-Request-Method': 'GET'
                                })

        # Assert response status_code.
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)

    def test_valid_cors_get_request(self):
        response = self.get('/v1/',
                            headers={
                                'Origin': 'http://valid.example.com'
                            })

        # Assert response status_code.
        self.assertEqual(response.status_code, 200)
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertEqual('http://valid.example.com',
                         response.headers['Access-Control-Allow-Origin'])

    def test_invalid_cors_get_request(self):
        response = self.get('/v1/',
                            headers={
                                'Origin': 'http://invalid.example.com'
                            })

        # Assert response status_code.
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)
