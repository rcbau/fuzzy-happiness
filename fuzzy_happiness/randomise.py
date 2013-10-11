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


_LOWERCASE_LETTERS = list(st.ascii_lowercase)
_UPPERCASE_LETTERS = list(st.ascii_uppercase)
_NUMERIC = list(st.digits)
_SYMBOLIC = list('!@#$%^&*()_-~`"\',./<>?:;\\|[]{}')
_ANY = _LOWERCASE_LETTERS + _UPPERCASE_LETTERS + _NUMERIC + _SYMBOLIC
_REPLACEMENT_DICTIONARY = {
    'lowercase_letters': (_LOWERCASE_LETTERS, _LOWERCASE_LETTERS),
    'uppercase_letters': (_UPPERCASE_LETTERS, _UPPERCASE_LETTERS),
    'numeric': (_NUMERIC, _NUMERIC),
    'symbolic': (_SYMBOLIC, _SYMBOLIC),
}

def random_char_replacement(character=None,
                            replacement_dictionary=_REPLACEMENT_DICTIONARY):
    if character is not None:
        for search, replace in replacement_dictionary.values():
            if character in search:
                if replace is None:
                    # Do no replace this character with anything
                    return character
                return random.choice(replace)

    return random.choice(_ANY)

def random_str_replacement(string,
                           replacement_dictionary=_REPLACEMENT_DICTIONARY,
                           padding_before=0,
                           padding_after=0):
    """Perform random character substitution on the provided string, allowing
       padding before and after, and an optional set of characters that can
       be used for substitution"""

    if string == None:
        return None

    string = list(string)

    for i, char in enumerate(string):
        string[i] = random_char_replacement(char)

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
        octet = str(random.randint(1,254))
        candidates.append(octet)
    return ".".join(candidates)


def randomness(old_value, column_type):
    """Generate a random value depending on the column_type using the
       old value as a reference for length and type"""
    # Note(mrda): TODO: Need to support datetime
    if column_type == 'ip_address':
        # Possibly need to make this smarter to keep subnet classes
        return random_ipaddress_replacement(old_value)
    elif column_type == 'hexstring':
        return random_str_replacement(old_value, keep_hexadecimal=True)
    elif column_type == 'hostname':
        replacement_dict = _REPLACEMENT_DICTIONARY.copy()
        replacement_dict['symbolic'] = (list('!@#$%^&*()~`"\',/<>?:;\\|[]{}'),
                                        _SYMBOLIC)
        replacement_dict['keep'] = (list('.-_'), None)
        return random_str_replacement(old_value,
                                      replacement_dictionary=replacement_dict)
    elif column_type in ('varchar', 'text', 'mediumtext'):
        return random_str_replacement(old_value)
    elif column_type in ('bigint', 'tinyint', 'int'):
        return random_str_replacement(old_value)
    elif column_type == 'float':
        replacement_dict = {
            'numeric': (_NUMERIC, _NUMERIC),
            'symbolic': (list('.'), None)
        }
        return random_str_replacement(old_value,
                                      replacement_dictionary=replacement_dict)
    else:
        return random_str_replacement(old_value)
