# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

import alembic
from alembic import config as alembic_config
from alembic import migration as alembic_migration

from kite.db.sqlalchemy import api as db_api


def _alembic_config():
    path = os.path.join(os.path.dirname(__file__), 'alembic.ini')
    config = alembic_config.Config(path)
    return config


def upgrade(revision=None, config=None):
    alembic.command.upgrade(config or _alembic_config(), revision or 'head')


def downgrade(revision=None, config=None):
    alembic.command.downgrade(config or _alembic_config(), revision or 'base')


def version(config=None):
    """Current database version.

    :returns: Database version
    :rtype: string
    """
    engine = db_api.get_engine()
    with engine.connect() as conn:
        context = alembic_migration.MigrationContext.configure(conn)
        return context.get_current_revision()
