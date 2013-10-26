#!/usr/bin/python
#
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

#
# SQL Data Anonymiser - proof of concept
#
# Still to do:
# 1) Need to write the reflection code to get at the docstrings to determine
#    which fields need anonymising
# 2) Need to write the anonymisation code for all data types.
#    'bonkers' is probably not a sufficient anonymisation value for all data
#    types :)
#

import os
import randomise
import re
import sys

from oslo.config import cfg

import attributes


opts = [
    cfg.BoolOpt('debug', default=False,
                help='Emit debug messages.')
]

CONF = cfg.CONF
CONF.register_opts(opts)


#
# SQL by regular expressions
# Note(mrda): If the SQL input format changes, these regexs will need changing
#             too
#
_re_blanks = re.compile(r'^(\s)*$')
_re_comments = re.compile(r'^((--)|(\/\*)).*')
_re_create_table = re.compile(r'^CREATE\sTABLE\s'
                              r'`(?P<table_name>([0-9A-Za-z_]+))`')
_re_end_create_table = re.compile(r'^\)\sENGINE=InnoDB')
_re_sql_I_dont_care_about = re.compile(r'^(LOCK|UNLOCK|DROP)')
_re_table_index = re.compile(r'^\s*`(?P<index_name>([A-Za-z_0-9]+))`\s+'
                             r'(?P<index_type>([A-Za-z_]+(\([0-9]+\))*))\s*')
_re_unneeded_table_sql = re.compile(r'^\s*((PRIMARY\sKEY)|(KEY)|(CONSTRAINT)|'
                                    r'(UNIQUE\sKEY))')
_re_insert = re.compile(r'^\s*INSERT\sINTO\s`(?P<table_name>([A-Za-z_0-9]+))`'
                        r'\sVALUES\s(?P<insert_values>(.*));')

# Regex to pull apart SQL types
_re_sql_types = re.compile(r'^(?P<typename>([a-zA-Z]+))'
                           r'(\((?P<typesize>([1-9]?[0-9]+))\))?')

#
# Static definition of which data fields should be anonymised
# Note(mrda): TODO: Need to build this programatically from the parsed
# docstrings.  See https://github.com/mikalstill/nova/blob/anonymise/nova/db/
#                  sqlalchemy/models.py
# as an example
#
## <<< START TEST DATA >>>
#
# Note(mrda): TODO: Need to test:
#   'bigint' type anonymisation
#
_anon_fields = {}
_anon_fields['compute_nodes'] = {}
_anon_fields['instance_types'] = {}
_anon_fields['fixed_ips'] = {}
_anon_fields['certificates'] = {}
_anon_fields['instance_actions_events'] = {}
# Testing int, bigint, tinyint
_anon_fields['compute_nodes']['vcpus'] = {"type": "int(11)"}
_anon_fields['fixed_ips']['allocated'] = {"type": "tinyint(1)"}
# Testing mediumtext, varchar, text
_anon_fields['compute_nodes']['cpu_info'] = {"type": "mediumtext"}
# TODO: certificates:user_id is actually a hex string and needs quoting.
#       This should be handled.
_anon_fields['certificates']['user_id'] = {"type": "hexstring"}
_anon_fields['instance_actions_events']['traceback'] = {"type": "text"}
# Testing float
_anon_fields['instance_types']['rxtx_factor'] = {"type": "float"}
## <<< END TEST DATA >>>

_UNDEF = "UNDEFINED"


# Note(mrda): These globals should be passed around rather than referenced
#             globally
_current_table_name = _UNDEF
_current_table_index = 0
_schema = {}
_type_table = {}


def process_line(line):
    """ Process each line in a mini state machine """

    # Oh, the shame
    global _current_table_name
    global _current_table_index
    global _schema
    global _type_table

    # Skip comments and blanks and things I don't care about
    if _re_blanks.match(line) or _re_comments.match(line) or \
        _re_sql_I_dont_care_about.match(line):
            return line

    # Find tables to build indexes
    m = _re_create_table.search(line)
    if m:
        _current_table_name = m.group("table_name")
        if _current_table_index not in _schema.keys():
            _schema[_current_table_name] = {}
        return line

    # Once we're in a table definition, get the row definitions
    if _current_table_name != _UNDEF:

        # Skip table defns I don't care about
        if _re_unneeded_table_sql.match(line):
            return line

        m = _re_table_index.search(line)
        if m:
            _current_table_index += 1
            _schema[_current_table_name][_current_table_index] = \
                {'name': m.group("index_name"),
                 'type': m.group("index_type")}
            if m.group("index_type") not in _type_table.keys():
                _type_table[m.group("index_type")] = 0
            else:
                _type_table[m.group("index_type")] += 1

            return line

    # Find the end of tables
    m = _re_end_create_table.match(line)
    if _current_table_name != _UNDEF and m:
        _current_table_name = _UNDEF
        _current_table_index = 0
        return line

    # Insert statements.  You will never find a more wretched hive
    # of scum and villainy.
    #
    # Also where the data is that needs anonymising is
    m = _re_insert.search(line)
    if m:
        return _parse_insert_data(m.group("table_name"),
                                  m.group("insert_values"),
                                  line)


def _parse_insert_data(table, values, line):
    """ Parse INSERT values, anonymising where required """
    elems = re.split('\),\(', values)
    i = 0
    anon_elems = []

    for elem in elems:
        if elem[0] == '(':
            elem = elem[1:]
        if elem[-1] == ')':
            elem = elem[:-1]
        anon_elems.append(_anonymise(elem, i, table))
        i += 1
    anonymised_str = '),('.join(anon_elems)
    return 'INSERT INTO `' + table + '` VALUES (' + anonymised_str + ');\n'


def _anonymise(line, table_index, table):
    """ Anonymise the supplied line if this table needs anonymising """
    # Need to find if any columns from table need anonymising
    if table in _anon_fields.keys():
        # we have anonymising to do!
        row_elems = re.split(',', line)

        for field_key in _anon_fields[table]:
            # Find the indexes we're interested in
            # i.e. where is this field?
            for idx in _schema[table]:
                if _schema[table][idx]['name'] == field_key:
                    # Anonymise
                    row_elems[idx] = _transmogrify(row_elems[idx],
                                                   _schema[table][idx]['type'])
        return ",".join(row_elems)
    else:
        # Give back the line unadultered, no anonymising for this table
        return line


def _dump_stats(filename):
    global _schema
    global _type_table

    print "\nStatistics for file `" + filename + "`\n"
    # Traverse the _schema
    print "Table Statistics"
    for table in _schema:
        print ("Table `" + table + "` has " + str(len(_schema[table].keys())) +
               " rows.")
    # Print the type table
    print "\nTypes found in SQL Schema"
    for key in _type_table:
        print key, "appears", _type_table[key], "times"


def _transmogrify(string, strtype):
    """ Anonymise the provide string, based upon it's strtype """
    # Note(mrda): TODO: handle mapping
    # Note(mrda): TODO: handle JSON and other embedded rich data structures (if
    #                   reqd)

    # Handle quoted strings
    need_single_quotes = False
    if string[0] == "'" and string[-1] == "'":
        need_single_quotes = True
        string = string[1:-1]

    typeinfo = strtype
    m = _re_sql_types.search(strtype)
    if m:
        typeinfo = m.group('typename')
    randomised = randomise.randomness(string, typeinfo)
    if need_single_quotes:
        randomised = "'" + randomised + "'"
    return randomised


filename_opt = cfg.StrOpt('filename',
                          default=None,
                          help='The filename to process',
                          positional=True)


def main():
    CONF.register_cli_opt(filename_opt)
    CONF(sys.argv[1:],
         project='fuzzy-happiness')

    if not CONF.filename:
        print 'Please specify a filename to process'
        return 1

    print 'Processing %s' % CONF.filename
    if not os.path.exists(CONF.filename):
        print 'Input file %s does not exist!' % CONF.filename
        return 1
    if not os.path.isfile(CONF.filename):
        print 'Input %s is not a file!' % CONF.filename
        return 1

    with open(CONF.filename, 'r') as r:
        output_filename = CONF.filename + ".output"
        with open(output_filename, 'w') as w:
            for line in r:
                w.write(process_line(line))

    if CONF.debug:
        _dump_stats(CONF.filename)

    return 0


if __name__ == '__main__':
    sys.exit(main())
