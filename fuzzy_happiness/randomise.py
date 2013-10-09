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

import random
import re
import string
import sys


def random_char_replacement(character='', keep_ascii=True,
                            keep_ascii_case=True, keep_whitespace=True,
                            keep_symbolic=True, keep_numeric=True):
    """Replace a character optionally keeping its type"""
    if character.isdigit() and keep_numeric:
        return random.randrange(9)
    elif character in string.ascii_letters and keep_ascii:
        if keep_ascii_case and character.islower():
            return random.choice(string.ascii_lowercase)
        elif keep_ascii_case and character.isupper():
            return random.choice(string.ascii_uppercase)
        else:
            return random.choice(string.ascii_letters)
    elif re.match(r'\s', character) and keep_whitespace:
        return character
    elif character not in string.ascii_letters and keep_symbolic:
        return random.choice(list('!@#$%^&*()_-~`"\',./<>?:;\\|[]{}'))
    else:
        return random.choice(list('!@#$%^&*()_-~`"\',./<>?:;\\|[]{}' +
                                  string.ascii_letters))


def random_str_replacement(string, padding_before=0, padding_after=0,
                           keep_ascii=True, keep_ascii_case=True,
                           keep_whitespace=True, keep_symbolic=True,
                           keep_numeric=True, exclude_characters=None):
    """Replace each character in a string optionally keep its type"""
     # Note(mrda): TODO: We need to potentially scan the string to determine
     # unspecified typing.  If a string looks like a hexstring, we should preserve
     # it even after randomisation
    string = list(string)
    for i, char in enumerate(string):
        if exclude_characters is None or char not in exclude_characters:
            string[i] = str(random_char_replacement(
                char, keep_ascii=keep_ascii,
                keep_ascii_case=keep_ascii_case,
                keep_whitespace=keep_whitespace,
                keep_symbolic=keep_symbolic,
                keep_numeric=keep_numeric
            ))

    for i in range(padding_before):
        string = random_char_replacement() + string

    for i in range(padding_after):
        string = string + random_char_replacement()

    return ''.join(string)


def randomness(old_value, column_type):
    """Generate a random value depending on the column_type using the
       old value as a reference for length and type"""
    # Note(mrda): TODO: Need to support datetime
    if column_type == 'ip_address':
        # Possibly need to make this smarter to keep subnet classes
        return random_str_replacement(old_value, exclude_characters='.')
    elif column_type == 'hostname':
        return random_str_replacement(old_value, exclude_characters='_-')
    elif column_type == 'varchar' or column_type == 'text' or \
       column_type == 'mediumtext':
        return random_str_replacement(old_value)
    elif column_type == 'bigint' or column_type == 'tinyint' or \
       column_type == 'int':
        return random_str_replacement(old_value, keep_numeric=True)
    elif column_type == 'float':
        return random_str_replacement(old_value, keep_numeric=True,
                                      keep_symbolic=True)
    else:
        return random_str_replacement(old_value)

