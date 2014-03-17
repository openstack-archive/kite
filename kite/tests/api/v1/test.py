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

from kite.tests.api.v1 import base


class TestVersion(base.BaseTestCase):

    def test_versions(self):
        resp = self.get('/')
        version = resp.json['version']
        self.assertEqual(resp.status_code, 200)

        host = 'http://localhost'  # webtest default

        self.assertEqual(version['id'], 'v1.0')
        self.assertEqual(version['status'], 'stable')
        self.assertEqual(version['links'][0]['href'], '%s/v1/' % host)
        self.assertEqual(version['links'][0]['rel'], 'self')
