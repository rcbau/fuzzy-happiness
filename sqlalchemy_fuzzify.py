
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from nova.db.sqlalchemy import models

import os
import random
import re
import string
import sys

import attributes


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
    # do something depending on column type
    # need more column types
    if column_type == 'ip_address':
        # Possibly need to make this smarter to keep subnet classes
        return random_str_replacement(old_value, exclude_characters='.')
    if column_type == 'hostname':
        return random_str_replacement(old_value, exclude_characters='_-')
    else:
        return random_str_replacement(old_value)


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
