fuzzy-happiness
===============

A SQL database anonymization tool

Setting up a test environment
=============================

Do something like this:

  sudo apt-get install virtualenvwrapper
  source /etc/bash_completion.d/virtualenvwrapper

  mkvirtualenv fh
  toggleglobalsitepackages
  python setup.py develop

To add parsing of anonymization attributes from models.py to this virtual
environment, we need to setup nova. This is a little ugly because setup.py
doesn't want to upgrade in place packages, so we install the dependancies
ourselves first. Be sure to do these steps whilst still in the fh venv.

  cd ...nova src dir...
  pip install -U -r requirements.txt
  python setup.py develop

We can test if things are working by asking the attributes parser to find us
an anonymization config:

  fhattributes

If that prints out a big dict of things, then you're set. You should be able
to run that command from anywhere (i.e. no specific path required) because of
having run "setup.py develop" in both directories.

Finally we can now anonymize a dataset:

  fhregexp ~/datasets/foo.sql