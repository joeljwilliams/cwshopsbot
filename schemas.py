#!/usr/bin/env python3

from marshmallow import Schema, fields, post_load
from models import Shop, Offer


class OfferSchema(Schema):
    shop = fields.Nested('ShopSchema')
    item = fields.Str()
    price = fields.Integer()
    mana = fields.Integer()

    @post_load
    def make_offer(self, data):
        return Offer(**data)


class ShopSchema(Schema):
    link = fields.Str()
    name = fields.Str()
    ownerName = fields.Str()
    ownerCastle = fields.Str()
    kind = fields.Str()
    mana = fields.Integer()
    offers = fields.Nested(OfferSchema, many=True, exclude=('shop',))

    @post_load
    def make_shop(self, data):
        return Shop(**data)

