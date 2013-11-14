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

import json
import random
import string as st
import uuid

_LOWERCASE_LETTERS = list(st.ascii_lowercase)
_UPPERCASE_LETTERS = list(st.ascii_uppercase)
_NUMERIC = list(st.digits)
_SYMBOLIC = list('!@#$%^&*()_-~`"\',./<>?:;\\|[]{}')
_WHITESPACE = list(st.whitespace)
_ANY = _LOWERCASE_LETTERS + _UPPERCASE_LETTERS + _NUMERIC + _SYMBOLIC
_REPLACEMENT_DICTIONARY = {
    'lowercase_letters': (_LOWERCASE_LETTERS, _LOWERCASE_LETTERS),
    'uppercase_letters': (_UPPERCASE_LETTERS, _UPPERCASE_LETTERS),
    'numeric': (_NUMERIC, _NUMERIC),
    'symbolic': (_SYMBOLIC, _SYMBOLIC),
    'whitespace': (_WHITESPACE, None)
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

    if string is None:
        return None

    string = list(str(string))

    for i, char in enumerate(string):
        string[i] = random_char_replacement(
            char, replacement_dictionary=replacement_dictionary)

    for i in range(padding_before):
        string = random_char_replacement(
            replacement_dictionary=replacement_dictionary) + string

    for i in range(padding_after):
        string = string + random_char_replacement(
            replacement_dictionary=replacement_dictionary)

    return ''.join(string)


def random_hexstring_replacement(string, padding_before=0, padding_after=0):
    """Randomise each character in a hexadecimal string"""
    replacement_dict = {
        'hex': (list(st.hexdigits), list(st.hexdigits))
    }
    return random_str_replacement(string, replacement_dict,
                                  padding_before, padding_after)


def random_pathname_replacement(string, padding_before=0, padding_after=0):
    """Randomise files and directories for a path, preserving directory
       structure"""
    # Note(mrda): Everything but /, \ and whitespace (while whitespace is
    # allowed in pathnames, it can prove diffficult to manage, so we won't
    # allow it for anonymisation
    allowed_chars = (st.ascii_letters + st.digits +
                     '!@#$%^&*()~`"\',<>?:;|[]{}')

    replacement_dict = _REPLACEMENT_DICTIONARY.copy()
    replacement_dict['symbolic'] = (allowed_chars, allowed_chars)
    replacement_dict['keep'] = (list('.-_/\\'), None)
    return random_str_replacement(string, replacement_dict,
                                  padding_before, padding_after)


def random_ipaddress_replacement(string, padding_before=0, padding_after=0):
    """Randomise each character in a IP Address string"""
    # Note(mrda): TODO: Should be extended for IPv6 addresses
    num_octets = len(string.split('.'))
    if num_octets not in [2, 3, 4]:
        # Not a valid IP Address
        return None
    candidates = []
    for i in range(num_octets):
        octet = str(random.randint(1, 254))
        candidates.append(octet)
    return ".".join(candidates)


def random_datetime_replacement(string):
    """Randomise a datetime string"""
    year = random.randint(1971, 2013)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # cheat
    hour = random.randint(0, 59)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return ("%04d-%02d-%02d %02d:%02d:%02d" %
           (year, month, day, hour, minute, second))


def random_json_replacement(string):
    """Randomise a json string"""
    if string[0] != '{':
        # Not json
        return random_str_replacement(string)

    json_obj = json.loads(string)

    # Note(mrda): Assuming a json dict, sorry
    for key in json_obj:
        if type(json_obj[key]) is dict:
            # Nested json goodness
            json_obj[key] = json.loads(
                random_json_replacement(json.dumps(json_obj[key])))
        else:
            json_obj[key] = random_str_replacement(json_obj[key])

    return json.dumps(json_obj)


def random_hostname_replacement(string):
    """Randomise a hostname"""
    # Valid hostname chars, according to RFC1123, is approximately
    # ([0-9a-z][0-9a-z\-]{0-62})(\.[0-9a-z][0-9a-z\-]{0-62})+
    # We'll simplify here
    allowed_chars = list('abcdefghijklmnopqrstuvwxyz0123456789')
    keep_chars = list('-.')
    replacement_dict = {
        'hostname': (allowed_chars, allowed_chars),
        'whitespace': (_WHITESPACE, None),
        'keep': (keep_chars, None)
    }
    return random_str_replacement(string, replacement_dict)


def randomness(old_value, column_type):
    """Generate a random value depending on the column_type using the
       old value as a reference for length and type"""

    # Special case randomisations
    if old_value == 'NULL' or old_value.strip() == "":
        return old_value
    if column_type == 'uuid':
        new_uuid = "'fake%s'" % str(uuid.uuid4())[5:]
        return new_uuid

    # Note(mrda): TODO: The following types are not yet implemented here:
    #     ec2_id
    #     integer
    #     ip_addesss_v6
    #     key_name
    if (column_type == 'ip_address_v4' or
        column_type == 'ip_address'):
        # Note(mikal): Possibly make this smarter to keep subnet classes
        return random_ipaddress_replacement(old_value)
    elif column_type == 'ip_address_v6':
        # Note(mrda): TODO: implement V6
        return old_value
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
    elif column_type in ('bigint', 'tinyint', 'int', 'long'):
        return random_str_replacement(old_value)
    elif column_type == 'float':
        replacement_dict = {
            'numeric': (_NUMERIC, _NUMERIC),
            'symbolic': (list('.'), None)
        }
        return random_str_replacement(old_value,
                                      replacement_dictionary=replacement_dict)
    elif column_type == 'datetime':
        return random_datetime_replacement(old_value)
    elif column_type == 'hostname':
        return random_hostname_replacement(old_value)
    elif old_value[0] == '{':
        # If it looks like json...
        return random_json_replacement(old_value)
    else:
        return random_str_replacement(old_value)
