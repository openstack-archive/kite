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

"""Initialize Kite Tables

Revision ID: 49c8b865f6b
Revises: None
Create Date: 2014-04-01 14:31:06.415935

"""

# revision identifiers, used by Alembic.
revision = '49c8b865f6b'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('hosts',
                    sa.Column('id',
                              sa.Integer(),
                              primary_key=True,
                              autoincrement=True),
                    sa.Column('name',
                              sa.Text(),
                              nullable=False),
                    sa.Column('group',
                              sa.Boolean(),
                              nullable=False),
                    sa.Column('latest_generation',
                              sa.Integer(),
                              nullable=False),
                    mysql_engine='InnoDB',
                    mysql_charset='utf8')

    op.create_index('name_idx', 'hosts', ['name'],
                    unique=True, mysql_length=20)

    op.create_table('keys',
                    sa.Column('host_id',
                              sa.Integer(),
                              sa.ForeignKey('hosts.id'),
                              primary_key=True,
                              autoincrement=False),
                    sa.Column('generation',
                              sa.Integer(),
                              primary_key=True,
                              autoincrement=False),
                    sa.Column('signature',
                              sa.LargeBinary(),
                              nullable=False),
                    sa.Column('enc_key',
                              sa.LargeBinary(),
                              nullable=False),
                    sa.Column('expiration',
                              sa.DateTime(),
                              nullable=True,
                              index=True),
                    mysql_engine='InnoDB',
                    mysql_charset='utf8')


def downgrade():
    op.drop_table('keys')
    op.drop_table('hosts')
