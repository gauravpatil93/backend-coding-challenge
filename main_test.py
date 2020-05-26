# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import main
import unittest


class TestApp(unittest.TestCase):

    def test_empty_query(self):
        main.app.testing = True
        client = main.app.test_client()
        r = client.get('/suggestions?q=')
        string = r.data.decode("utf-8").strip()
        string = string.replace('"', "")
        self.assertEqual("length of value must be at least 1 for dictionary value @ data['q']", string)

    def test_no_query(self):
        main.app.testing = True
        client = main.app.test_client()
        r = client.get('/suggestions')
        string = r.data.decode("utf-8").strip()
        string = string.replace('"', "")
        self.assertEqual("required key not provided @ data['q']", string)

    def test_no_query_equals(self):
        main.app.testing = True
        client = main.app.test_client()
        r = client.get('/suggestions?')
        string = r.data.decode("utf-8").strip()
        string = string.replace('"', "")
        self.assertEqual("required key not provided @ data['q']", string)

    def test_no_output(self):
        main.app.testing = True
        client = main.app.test_client()
        r = client.get('/suggestions?q=somerandomplace')
        response = '{suggestions: []}'
        string = r.data.decode("utf-8").strip()
        string = string.replace('"', "")
        self.assertEqual(response, string)

    def test_query_is_number_output(self):
        main.app.testing = True
        client = main.app.test_client()
        r = client.get('/suggestions?q=12345')
        response = '{suggestions: []}'
        string = r.data.decode("utf-8").strip()
        string = string.replace('"', "")
        self.assertEqual(response, string)
    

if __name__ == '__main__':
    unittest.main()
