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

from oslo.config import cfg
from sqlalchemy.orm import exc

from kite.common import exception
from kite.db import connection
from kite.db.sqlalchemy import models
from kite.openstack.common.db.sqlalchemy import session as db_session

CONF = cfg.CONF
_facade = None


def get_facade():
    global _facade
    if not _facade:
        _facade = db_session.EngineFacade.from_config(CONF.database.connection,
                                                      CONF)
    return _facade


def reset(self):
    global _facade
    _facade = None


def get_backend():
    return SqlalchemyDbImpl()


class SqlalchemyDbImpl(connection.Connection):

    def __init__(self, sessionmaker=None):
        self.sessionmaker = sessionmaker

    def get_session(self, **kwargs):
        if self.sessionmaker:
            return self.sessionmaker(**kwargs)
        return get_facade().get_session(**kwargs)

    def set_key(self, name, key, signature, group, expiration=None):
        session = self.get_session()

        with session.begin():
            q = session.query(models.Host)
            q = q.filter(models.Host.name == name)

            try:
                host = q.one()
            except exc.NoResultFound:
                host = models.Host(name=name,
                                   latest_generation=0,
                                   group=group)
            else:
                if host.group != group:
                    raise exception.GroupStatusChanged(name=name)

            host.latest_generation += 1
            host.keys.append(models.Key(signature=signature,
                                        enc_key=key,
                                        generation=host.latest_generation,
                                        expiration=expiration))

            session.add(host)

        return host.latest_generation

    def get_key(self, name, generation=None, group=None):
        session = self.get_session()

        query = session.query(models.Host, models.Key)
        query = query.filter(models.Host.id == models.Key.host_id)
        query = query.filter(models.Host.name == name)

        if group is not None:
            query = query.filter(models.Host.group == group)

        if generation is not None:
            query = query.filter(models.Key.generation == generation)
        else:
            query = query.filter(models.Host.latest_generation ==
                                 models.Key.generation)

        try:
            result = query.one()
        except exc.NoResultFound:
            return None

        return {'name': result.Host.name,
                'group': result.Host.group,
                'key': result.Key.enc_key,
                'signature': result.Key.signature,
                'generation': result.Key.generation,
                'expiration': result.Key.expiration}
