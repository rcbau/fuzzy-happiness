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


CONF = cfg.CONF

opts = [
    cfg.BoolOpt('add_descriptive_comments',
                default=True,
                help=('Add comments to output describing what we did to a '
                      'given table.'))
]
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

# Note(mrda): TODO: Need to test:
#   'bigint' type anonymisation
#

_UNDEF = "UNDEFINED"


class Fuzzer(object):
    def __init__(self, anon_fields):
        self.anon_fields = anon_fields
        self.cur_table_name = _UNDEF
        self.cur_table_index = 0
        self.schema = {}
        self.type_table = {}

    def process_line(self, line):
        """ Process each line in a mini state machine """

        # Skip comments and blanks and things I don't care about
        if (_re_blanks.match(line) or _re_comments.match(line) or
            _re_sql_I_dont_care_about.match(line)):
            if CONF.debug:
                print '    ...unimportant line'
            return line

        # Find tables to build indexes
        m = _re_create_table.search(line)
        if m:
            self.cur_table_name = m.group("table_name")
            if self.cur_table_index not in self.schema:
                self.schema[self.cur_table_name] = {}
            if CONF.debug:
                print '    ...table definition starts'
            return line

        # Once we're in a table definition, get the row definitions
        if self.cur_table_name != _UNDEF:
            # Skip table defns I don't care about
            if _re_unneeded_table_sql.match(line):
                if CONF.debug:
                    print '    ...non-column table definition'
                return line

            m = _re_table_index.search(line)
            if m:
                self.cur_table_index += 1
                self.schema[self.cur_table_name][self.cur_table_index] = \
                    {'name': m.group("index_name"),
                     'type': m.group("index_type")}

                self.type_table.setdefault(m.group("index_type"), 0)
                self.type_table[m.group("index_type")] += 1

                if CONF.debug:
                    print '    ...schema: %s = %s' % (m.group("index_name"),
                                                      m.group("index_type"))
                return line

        # Find the end of tables
        m = _re_end_create_table.match(line)
        if self.cur_table_name != _UNDEF and m:
            additional = []
            if CONF.add_descriptive_comments:
                for idx in self.schema[self.cur_table_name]:
                    col_name = self.schema[self.cur_table_name][idx]['name']
                    config = self.anon_fields.get(self.cur_table_name, {})

                    anon_type = config.get(col_name)
                    anon_str = ''
                    if anon_type:
                        anon_str = ' (anonymized as %s)' % anon_type
                    
                    additional.append(
                        '/* Fuzzy happiness field %s named %s is %s%s */'
                        %(idx, col_name,
                          self.schema[self.cur_table_name][idx]['type'],
                          anon_str))

            self.cur_table_name = _UNDEF
            self.cur_table_index = 0
            if CONF.debug:
                print '    ...end of table definition'

            if additional:
                line += '\n%s\n\n' % '\n'.join(additional)

            return line

        # Insert statements.  You will never find a more wretched hive
        # of scum and villainy.
        #
        # Also where the data is that needs anonymising is
        m = _re_insert.search(line)
        if m:
            if CONF.debug:
                print '    ...data bearing line'
            return self._parse_insert_data(m.group("table_name"),
                                           m.group("insert_values"),
                                           line)

    def _parse_insert_data(self, table, values, line):
        """ Parse INSERT values, anonymising where required """
        elems = re.split('\),\(', values)
        i = 0
        anon_elems = []

        for elem in elems:
            if elem[0] == '(':
                elem = elem[1:]
            if elem[-1] == ')':
                elem = elem[:-1]
            anon_elems.append(self._anonymise(elem, i, table))
            i += 1
        anonymised_str = '),\n    ('.join(anon_elems)
        return ('INSERT INTO `' + table + '` VALUES \n    (' +
                anonymised_str + ');\n')

    def _anonymise(self, line, table_index, table):
        """ Anonymise the supplied line if this table needs anonymising """
        # Need to find if any columns from table need anonymising
        if not table in self.anon_fields:
            return line

        row_elems = re.split(',', line)

        for field_key in self.anon_fields[table]:
            # Find the indexes we're interested in
            # i.e. where is this field?
            for idx in self.schema[table]:
                if self.schema[table][idx]['name'] == field_key:
                    # Anonymise
                    row_elems[idx - 1] = self._transmogrify(
                        row_elems[idx - 1], self.schema[table][idx]['type'])
        return ",".join(row_elems)

    def dump_stats(self, filename):
        print "\nStatistics for file `" + filename + "`\n"
        # Traverse the self.schema
        print "Table Statistics"
        for table in self.schema:
            print ("Table `" + table + "` has " +
                   str(len(self.schema[table])) + " rows.")
        # Print the type table
        print "\nTypes found in SQL Schema"
        for key in self.type_table:
            print key, "appears", self.type_table[key], "times"

    def _transmogrify(self, string, strtype):
        """ Anonymise the provide string, based upon it's strtype """
        # Note(mrda): TODO: handle mapping
        # Note(mrda): TODO: handle JSON and other embedded rich data
        #                   structures (if reqd)

        if CONF.debug:
            print ('    ....transmogrifying string "%s" of type %s'
                   %(string, strtype))

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
    CONF(sys.argv[1:], project='fuzzy-happiness')

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

    # Load attributes from models.py
    anon_fields = attributes.load_configuration()
    fuzz = Fuzzer(anon_fields)

    with open(CONF.filename, 'r') as r:
        output_filename = CONF.filename + ".output"
        with open(output_filename, 'w') as w:
            for line in r:
                processed = fuzz.process_line(line)
                if CONF.debug:
                    print '>>> %s' % line.rstrip()
                    print '<<< %s' % processed.rstrip()
                w.write(processed)

    if CONF.debug:
        fuzz.dump_stats(CONF.filename)

    return 0
