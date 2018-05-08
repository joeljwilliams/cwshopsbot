#!/usr/bin/env python3

from telegram import User
from pony import orm


class TgMixin:
    @classmethod
    def update_or_create(cls, obj):
        if isinstance(obj, User):
            params = obj.to_dict()
        elif isinstance(obj, dict):
            params = obj

        try:
            # try retrieve object via primary key
            instance = cls[tuple(
                params[pk_attr.name]
                for pk_attr in cls._pk_attrs_
            )]
        except orm.ObjectNotFound:
            # if object not found, create and return it
            return cls(**params)
        else:
            # else it was found, lets update existing params and unset missing params
            newparams = {k.name: params.setdefault(k.name, k.py_type()) for k in cls._attrs_}
            instance.set(**newparams)

            return instance
