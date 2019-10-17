"""
Iko (移行) is an asynchronous micro-framework
for converting data into different structures.

Use load to marshal from request to mongo.
Use dump to marshal from mongo to response.
"""
from typing import Dict


OPTIONAL = object()


class Field:
    def __init__(
            self,
            required=False,
            default=OPTIONAL,
            dump_to=None,
            load_from=None,
    ):
        if required:
            assert default == OPTIONAL
        self.required = required
        self.default = default
        self.dump_to = dump_to
        self.load_from = load_from

    async def dump(self, data, attr, context):
        if self.required:
            return data[attr]
        return data.get(attr, self.default)

    async def load(self, data, attr, context):
        if self.required:
            return data[attr]
        return data.get(attr, self.default)


class Nested(Field):
    def __init__(
            self,
            schema: 'Schema',
            required=False,
            default=OPTIONAL,
            dump_to=None,
            load_from=None,
    ):
        self.schema = schema
        super().__init__(required, default, dump_to, load_from)

    async def dump(self, data, attr, context):
        value = await super().dump(data, attr, context)
        if value == OPTIONAL:
            return value
        return await self.schema.dump(value, context)


class List(Field):
    def __init__(
            self,
            schema: 'Schema' = None,
            required=False,
            dump_to=None,
            load_from=None,
    ):
        self.schema = schema
        super().__init__(required, dump_to=dump_to, load_from=load_from)

    async def dump(self, data, attr, context):
        value = await super().dump(data, attr, context)
        if value == OPTIONAL:
            return value
        return [
            await self.schema.dump(item, context) if self.schema else item
            for item in value
        ]

    async def load(self, data, attr, context):
        value = await super().load(data, attr, context)
        if value == OPTIONAL:
            return value
        return [
            await self.schema.load(item) if self.schema else item
            for item in value
        ]


class SchemaMeta(type):
    def __new__(mcs, name, bases, attrs):
        fields = {}
        for base in bases:
            if issubclass(base, Schema):
                fields.update(base.__fields__)
        fields.update({
            name: field
            for name, field in attrs.items()
            if isinstance(field, Field)
        })
        attrs['__fields__'] = fields
        return super().__new__(mcs, name, bases, attrs)


class Schema(metaclass=SchemaMeta):
    __fields__: Dict[str, Field]

    @classmethod
    async def dump(cls, data, context=None):
        result = {}
        for attr, field in cls.__fields__.items():
            value = await field.dump(data, attr, context)
            if value != OPTIONAL:
                result[field.dump_to or attr] = value
        return result

    @classmethod
    async def load(cls, data, context=None):
        result = {}
        for attr, field in cls.__fields__.items():
            value = await field.load(
                data,
                field.load_from if field.load_from else attr,
                context,
            )
            if value != OPTIONAL:
                result[attr] = value
        return result
