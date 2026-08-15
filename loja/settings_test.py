"""Test settings.

The production database user has no CREATEDB grant, so the suite runs on an
in-memory SQLite database. Row-level locking (``select_for_update``) is a no-op
on SQLite, so concurrency behaviour must be verified against PostgreSQL before
release; everything else in the suite is engine-independent.
"""

from loja.settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
DEBUG = False
