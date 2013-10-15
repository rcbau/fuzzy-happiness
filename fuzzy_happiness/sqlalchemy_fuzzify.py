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

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from nova.db.sqlalchemy import models
from nova.db.sqlalchemy import utils
from migrate import ForeignKeyConstraint

import attributes
from randomise import randomness


# hacky, make not global
fkey_onupdate_restore = {}


def cascade_fkeys(metadata):
    """ Sets all fkeys to cascade on update """
    global fkey_onupdate_restore
    for table_name, table in metadata.tables.items():
        for fkey in list(table.foreign_keys):
            params = {
                'columns': fkey.constraint.columns,
                'refcolumns': [fkey.column],
                'name': fkey.constraint.name,
                'onupdate': fkey.constraint.onupdate,
                'ondelete': fkey.constraint.ondelete,
                'deferrable': fkey.constraint.deferrable,
                'initially': fkey.constraint.initially,
                'table': table
            }
            fkey_onupdate_restore[fkey.constraint.name] = \
                fkey.constraint.onupdate

            fkey_constraint = ForeignKeyConstraint(**params)
            fkey_constraint.drop()

            params['onupdate'] = 'CASCADE'
            fkey_constraint = ForeignKeyConstraint(**params)
            fkey_constraint.create()


def restore_fkeys(metadata):
    """ Restores the old cascade settings for each table """
    global fkey_onupdate_restore
    for table_name, table in metadata.tables.items():
        for fkey in list(table.foreign_keys):
            if fkey.constraint.name in fkey_onupdate_restore:
                params = {
                    'columns': fkey.constraint.columns,
                    'refcolumns': [fkey.column],
                    'name': fkey.constraint.name,
                    'onupdate': fkey.constraint.onupdate,
                    'ondelete': fkey.constraint.ondelete,
                    'deferrable': fkey.constraint.deferrable,
                    'initially': fkey.constraint.initially,
                    'table': table
                }
                fkey_constraint = ForeignKeyConstraint(**params)
                fkey_constraint.drop()

                params['onupdate'] = \
                    fkey_onupdate_restore[fkey.constraint.name]
                fkey_constraint = ForeignKeyConstraint(**params)
                fkey_constraint.create()


def fuzzify(engine, config):
    """Do the actual fuzzification based on the loaded attributes of
       the models."""
    Session = sessionmaker(bind=engine)
    session = Session()
    metadata = MetaData(bind=engine, reflect=True)
    cascade_fkeys(metadata)

    for model_name, columns in config.items():
        table_name = getattr(models, model_name).__tablename__
        tables = [getattr(models, model_name)]
        if 'shadow_' + table_name in metadata.tables.keys():
            tables.append(utils.get_table(engine, 'shadow_' + table_name))
        for table in tables:
            q = session.query(table)
            for row in list(q.all()):
                for column, column_type in columns:
                    setattr(row, column,
                            randomness(getattr(row, column), column_type))

    session.commit()
    restore_fkeys(metadata)


if __name__ == '__main__':
    # Import the database to modify
    #os.system('mysql -u root nova_fuzzy < nova.sql')

    # Set up the session
    engine = create_engine('mysql://root:tester@localhost/nova_fuzzy',
                           echo=True)

    # Grab the randomisation commands
    config = attributes.load_configuration()

    # Perform fuzzification and save back to database
    fuzzify(engine, config)

    # Dump the modified database
    # os.system('mysqldump -u root nova_fuzzy > nova_fuzzy.sql')
