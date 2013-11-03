#!/usr/bin/python

import datetime
import re
import sqlparse
import sys

#import attributes


TABLE_NAME_RE = re.compile('CREATE TABLE `(.+)`')
COLUMN_RE = re.compile('  `(.+)` ([^ ,]+).*')


class DumpProcessor(object):
    def __init__(self, input_path, output_path, anon_fields):
        self.input_path = input_path
        self.output_path = output_path
        self.anon_fields = anon_fields

    def read_sql_dump(self):
        """Read a SQL dump file and process it."""

        # Optimization -- read blocks, separating by blank lines. Each block
        # is parsed as a group.
        with open(self.input_path) as f:
            with open(self.output_path, 'w') as self.out:
                pre_insert = []
                inserts = []
                post_insert = []

                l = f.readline()
                while l:
                    if not l.startswith('-- Table structure for'):
                        if l.startswith('INSERT'):
                            inserts.append(l)
                        elif not inserts:
                            pre_insert.append(l)
                        else:
                            post_insert.append(l)
                    else:
                        post_insert.append(l)
                        self.parse_block(''.join(pre_insert), inserts,
                                         ''.join(post_insert))
                        pre_insert = []
                        inserts = []
                        post_insert = []

                    l = f.readline()

                if pre_insert or inserts or post_insert:
                    self.parse_block(''.join(pre_insert), inserts,
                                     ''.join(post_insert))

    def parse_block(self, pre_insert, inserts, post_insert):
        """Parse one of these blocks that we've extracted."""

        # Special case empty tables
        if not inserts:
            self.out.write(pre_insert)
            self.out.write(''.join(inserts))
            self.out.write(post_insert)
            return

        self.out.write(pre_insert)
        create_statement = self.extract_create(pre_insert)
        if not create_statement and inserts:
            print 'Error! How can we have inserts without a create?'
            print 'PRE %s' % pre_insert
            for insert in inserts:
                print 'INS %s' % insert
            print 'PST %s' % post_insert
            sys.exit(1)

        if create_statement:
            table_name, columns = self.parse_create(create_statement)

        for insert in inserts:
            self.handle_insert(table_name, columns, insert)

        self.out.write(post_insert)

    def extract_create(self, pre_insert):
        """Extract the create statement from a block of SQL."""

        # This method is over engineered. If we're just looking for creates we
        # could just filter this more aggressively. However, I wanted to
        # understand what the other tokens were before I did that, and now I
        # have all this code...
        create_data = []

        ignore_statement = False
        create_statement = False
        for parse in sqlparse.parse(pre_insert):
            for token in parse.tokens:
                # End of statement
                if token.value in [';']:
                    ignore_statement = False
                    create_statement = False
                    continue

                # If we've decided to ignore this entire statement, then do
                # that
                if ignore_statement:
                    continue

                if token.is_whitespace():
                    continue

                # Capture create details
                if create_statement:
                    create_data.append(token.value)
                    continue

                # Filter out boring things
                if isinstance(token, sqlparse.sql.Comment):
                    continue
                if str(token.ttype) in ['Token.Comment.Single']:
                    continue
                if token.value in ['LOCK', 'UNLOCK']:
                    ignore_statement = True
                    continue

                # DDL is special
                if str(token.ttype) == 'Token.Keyword.DDL':
                    if token.value == 'DROP':
                        ignore_statement = True
                        continue
                    if token.value == 'CREATE':
                        create_data.append(token.value)
                        create_statement = True
                        continue

                print 'Unknown parser token!'
                print token
                print dir(token)
                print 'ttype: %s = >>%s<<' % (str(token.ttype), token.value)
                print '    %s: %s' % (type(token), repr(token))

        return ' '.join(create_data)

    def parse_create(self, create_statement):
        """Parse a create statement.

        Returns the name of the table and a list of tuples. Each tuple is
        the name of the column and the type.
        """

        # sqlparse falls apart when you ask it to parse DDL. It thinks that
        # the DDL statement is a function, and doesn't quite know what to do.
        # So, we're going to revert to something more basic for creates.
        table_name = None
        columns = []

        for line in create_statement.split('\n'):
            m = TABLE_NAME_RE.match(line)
            if m:
                table_name = m.group(1)

            m = COLUMN_RE.match(line)
            if m:
                columns.append((m.group(1), m.group(2)))

        return table_name, columns

    def handle_insert(self, table_name, columns, insert):
        """Parse an insert statement into its rows."""

        for parse in sqlparse.parse(insert):
            for token in parse.tokens:
                if not isinstance(token, sqlparse.sql.Parenthesis):
                    continue

                row = []
                for subtoken in token.tokens:
                    if not isinstance(subtoken, sqlparse.sql.IdentifierList):
                        continue

                    for ident in subtoken.tokens:
                        if str(ident.ttype) == 'Token.Punctuation':
                            continue
                        row.append(ident.value)

                if row:
                    self.anonymize_row(table_name, columns, row)

    def anonymize_row(self, table_name, columns, row):
        """Handle a single row."""

        if len(columns) != len(row):
            print 'Error: How did we end up with the wrong number of columns?'
            sys.exit(1)

        print table_name
        counter = 0
        for column in row:
            print '    %s %s = %s' % (columns[counter][0],
                                    columns[counter][1],
                                    column)
            counter += 1


if __name__ == '__main__':
    #anon_fields = attributes.load_configuration()

    anon_fields = {}
    dp = DumpProcessor('/home/mikal/datasets/nova_user_001.sql',
                       '/tmp/nova_user_001.sql.post',
                       anon_fields)
    dp.read_sql_dump()
