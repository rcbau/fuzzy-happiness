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
import string as st
import sys


def random_char_replacement(character='', keep_ascii=True,
                            keep_ascii_case=True, keep_whitespace=True,
                            keep_symbolic=True, keep_numeric=True,
                            allowed_chars=None):

    if allowed_chars: # ignore all other options
        return random.choice(allowed_chars)

    if character in st.ascii_letters and keep_ascii:
        if keep_ascii_case and character.islower():
            return random.choice(st.ascii_lowercase)
        elif keep_ascii_case and character.isupper():
            return random.choice(st.ascii_uppercase)
        else:
            return random.choice(st.ascii_letters)
    elif re.match(r'\s', character) and keep_whitespace:
        return character # don't substitute whitespace
    elif character not in st.ascii_letters and keep_symbolic:
        return random.choice(list('!@#$%^&*()_-~`"\',./<>?:;\\|[]{}'))
    elif character in st.digits and keep_numeric:
        return random.choice(list(st.digits))
    else:
        return random.choice(list('!@#$%^&*()_-~`"\',./<>?:;\\|[]{}' +
                                  st.ascii_letters +
                                  st.digits))


def random_str_replacement(string,
                           allowed_chars=st.ascii_letters,
                           exclude_chars=None,
                           padding_before=0,
                           padding_after=0):
    """Perform random character substitution on the provided string, allowing
       padding before and after, and an optional set of characters that can
       be used for substitution"""

    if string == None:
        return None

    string = list(string)

    for i, char in enumerate(string):
        if exclude_chars is None or char not in exclude_chars:
            string[i] = random_char_replacement(char,
                                allowed_chars=allowed_chars)

    for i in range(padding_before):
        string = random_char_replacement() + string

    for i in range(padding_after):
        string = string + random_char_replacement()

    return ''.join(string)


def random_hexstring_replacement(string, padding_before=0, padding_after=0):
    """Randomise each character in a hexadecimal string"""
    return random_str_replacement(string, 'abcdef0123456789', None,
                                  padding_before, padding_after)


def random_pathname_replacement(string, padding_before=0, padding_after=0):
    """Randomise files and directories for a path, preserving directory
       structure"""
    # Note(mrda): Everything but /, \ and whitespace (while whitespace is
    # allowed in pathnames, it can prove diffficult to manage, so we won't
    # allow it for anonymisation
    allowed_chars = (st.ascii_letters + st.digits +
                     '!@#$%^&*()_-~`"\',.<>?:;|[]{}')

    return random_str_replacement(string, allowed_chars, '\/\\',
                                  padding_before, padding_after)


def random_ipaddress_replacement(string, padding_before=0, padding_after=0):
    """Randomise each character in a IP Address string"""
    # Note(mrda): TODO: Should be extended for IPv6 addresses
    candidates = []
    for i in range(4):
        octet = ""
        while True:
            octet = random_str_replacement("123", st.digits)
            if int(octet) < 255:
                break
        candidates.append(octet)
    return ".".join(candidates)


def randomness(old_value, column_type):
    """Generate a random value depending on the column_type using the
       old value as a reference for length and type"""
    # Note(mrda): TODO: Need to support datetime
    if column_type == 'ip_address':
        # Possibly need to make this smarter to keep subnet classes
        return random_str_replacement(old_value, exclude_characters='.')
    elif column_type == 'hexstring':
        return random_str_replacement(old_value, keep_hexadecimal=True)
    elif column_type == 'hostname':
        return random_str_replacement(old_value, exclude_characters='_-')
    elif (column_type == 'varchar' or
          column_type == 'text' or
          column_type == 'mediumtext'):
        return random_str_replacement(old_value)
    elif (column_type == 'bigint' or
          column_type == 'tinyint' or
          column_type == 'int'):
        return random_str_replacement(old_value, keep_numeric=True)
    elif column_type == 'float':
        return random_str_replacement(old_value, keep_numeric=True,
                                      exclude_characters='.')
    else:
        return random_str_replacement(old_value)

