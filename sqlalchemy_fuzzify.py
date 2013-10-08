
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
