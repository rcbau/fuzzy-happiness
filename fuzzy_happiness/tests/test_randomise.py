# Copyright 2013 Rackspace Australia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import testtools
import string

from randomise import random_char_replacement

class TestRandomCharReplacement(testtools.TestCase):

    def test_simple_char(self):
        self.assertIn(random_char_replacement(
                'a',
                keep_ascii=True,
                keep_ascii_case=False,
                keep_whitespace=False,
                keep_symbolic=False,
                keep_numeric=False,
                keep_hexadecimal=False),
            list(string.ascii_letters))

    def test_simple_digit(self):
        self.assertIn(random_char_replacement(
                '6',
                keep_ascii=False,
                keep_ascii_case=False,
                keep_whitespace=False,
                keep_symbolic=False,
                keep_numeric=True,
                keep_hexadecimal=False),
            list(string.digits))

class TestRandomStrReplacement(testtools.TestCase):

    def test_simple(self):
        pass

class TestRandomness(testtools.TestCase):

    def test_almost_simple(self):
        pass

