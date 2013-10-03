#!/usr/bin/python

# Read doc comments and work out what fields to anonymize


import inspect
import re

from nova.db.sqlalchemy import models


ANON_CONFIG_RE = re.compile('^ *:anon ([^ ]+): ([^ ]+)$')


def load_configuration():
    configs = {}

    for name, obj in inspect.getmembers(models):
        if not inspect.isclass(obj):
            continue

        if not issubclass(obj, models.NovaBase):
            continue

        if not obj.__doc__:
            continue

        attributes = []
        for line in obj.__doc__.split('\n'):
            m = ANON_CONFIG_RE.match(line)
            if m:
                attributes.append((m.group(1), m.group(2)))

        if attributes:
            configs[name] = attributes

    return configs


if __name__ == '__main__':
    print load_configuration()
