#!/usr/bin/env python3

from pony import orm
from mixins import TgMixin

import config

db = orm.Database()


class User(db.Entity, TgMixin):
    id = orm.PrimaryKey(int)
    first_name = orm.Required(str)
    is_bot = orm.Required(bool)
    last_name = orm.Optional(str)
    username = orm.Optional(str)
    language_code = orm.Optional(str)


class Offer(db.Entity):
    shop = orm.Required('Shop')
    item = orm.Required(str)
    price = orm.Required(int)
    mana = orm.Required(int)


class Shop(db.Entity):
    link = orm.Required(str)
    name = orm.Required(str)
    ownerName = orm.Required(str)
    ownerCastle = orm.Required(str)
    kind = orm.Required(str)
    mana = orm.Required(int)
    offers = orm.Set(Offer)


if config.APP_ENV and config.APP_ENV.startswith('PROD'):
    db.bind(**config.DB_PARAMS)
else:
    orm.set_sql_debug(True)
    db.bind('sqlite', 'shops.sqlite', create_db=True)
db.generate_mapping(create_tables=True)
