#!/usr/bin/python2
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

import os

import attributes
from randomise import randomness

def fuzzify(session, config):
    """Do the actual fuzzification based on the loaded attributes of
       the models."""
    for table, columns in config.items():
        q = session.query(getattr(models, table))
        for row in q.all():
            for column, column_type in columns:
                setattr(row, column,
                        randomness(getattr(row, column), column_type))

if __name__ == '__main__':
    # Import the database to modify
    #os.system('mysql -u root nova_fuzzy < nova.sql')

    # Set up the session
    engine = create_engine('mysql://root:tester@localhost/nova_fuzzy', echo=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Grab the randomisation commands
    config = attributes.load_configuration()

    # Perform fuzzification and save back to database
    fuzzify(session, config)
    session.commit()

    # Dump the modified database
    # os.system('mysqldump -u root nova_fuzzy > nova_fuzzy.sql')
