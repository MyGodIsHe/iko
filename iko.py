import asyncio
from typing import Dict
from typing import Type

OPTIONAL = object()


class Field:
    def __init__(
            self,
            default=OPTIONAL,
            dump_to=None,
            load_from=None,
            outer_name=None,
    ):
        if outer_name is not None:
            assert dump_to is None and load_from is None
        self.default = default
        self.dump_to = dump_to or outer_name
        self.load_from = load_from or outer_name

    async def dump(self, data, attr, context):
        value = data.get(attr, self.default)
        if value == OPTIONAL:
            return value
        return await self.post_dump(value, context)

    async def post_dump(self, value, context):
        return value

    async def load(self, data, attr, context):
        value = data.get(attr, self.default)
        if value == OPTIONAL:
            return value
        return await self.post_load(value, context)

    async def post_load(self, value, context):
        return value


class Const(Field):
    def __init__(self, value):
        self.value = value
        super().__init__()

    async def dump(self, data, attr, context):
        return self.value

    async def load(self, data, attr, context):
        return self.value


class Nested(Field):
    def __init__(
            self,
            schema: Type['Schema'],
            default=OPTIONAL,
            dump_to=None,
            load_from=None,
            outer_name=None,
    ):
        self.schema = schema
        super().__init__(default, dump_to, load_from, outer_name)

    async def post_dump(self, value, context):
        return await self.schema.dump(value, context=context)


class List(Field):
    def __init__(
            self,
            schema: Type['Schema'] = None,
            default=OPTIONAL,
            dump_to=None,
            load_from=None,
            outer_name=None,
    ):
        self.schema = schema
        super().__init__(default, dump_to, load_from, outer_name)

    async def post_dump(self, value, context):
        return [
            (
                await self.schema.dump(item, context=context)
                if self.schema
                else item
            )
            for item in value
        ]

    async def post_load(self, value, context):
        return [
            (
                await self.schema.load(item, context=context)
                if self.schema
                else item
            )
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
    async def dump(cls, data, *, context=None):
        values = await asyncio.gather(*[
            field.dump(data, attr, context)
            for attr, field in cls.__fields__.items()
        ])
        attrs = [
            field.dump_to or attr
            for attr, field in cls.__fields__.items()
        ]
        return {
            attr: value
            for attr, value in zip(attrs, values)
            if value != OPTIONAL
        }

    @classmethod
    async def load(cls, data, *, context=None):
        values = await asyncio.gather(*[
            field.load(
                data,
                field.load_from if field.load_from else attr,
                context,
            )
            for attr, field in cls.__fields__.items()
        ])
        return {
            attr: value
            for attr, value in zip(cls.__fields__, values)
            if value != OPTIONAL
        }
