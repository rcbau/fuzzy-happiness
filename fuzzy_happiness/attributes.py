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


# Work out what fields to anonymize. To run a simple example, do this:
#     cd <nova checkout dir>
#     . .tox/py27/bin/activate
#     <path to fuzzy happiness>/attributes.py


import inspect

from nova.db.sqlalchemy import models


def load_configuration():
    configs = {}

    for name, obj in inspect.getmembers(models):
        if not inspect.isclass(obj):
            continue

        if not issubclass(obj, models.NovaBase):
            continue

        attrs_missing = []
        for required_attr in ['__tablename__', '__confidential__']:
            if not hasattr(obj, required_attr):
                attrs_missing.append(required_attr)

        if attrs_missing:
            print ('Required attributes %s missing from %s'
                   % (', '.join(attrs_missing), name))
            continue

        configs[obj.__tablename__] = obj.__confidential__

    return configs


if __name__ == '__main__':
    print load_configuration()
