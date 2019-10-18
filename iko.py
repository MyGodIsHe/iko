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
        return data.get(attr, self.default)

    async def load(self, data, attr, context):
        return data.get(attr, self.default)


class Const(Field):
    def __init__(self, value):
        self.value = value
        super().__init__()

    async def load(self, data, attr, context):
        return self.value


class Nested(Field):
    def __init__(
            self,
            schema: Type['Schema'],
            default=OPTIONAL,
            dump_to=None,
            load_from=None,
    ):
        self.schema = schema
        super().__init__(default, dump_to, load_from)

    async def dump(self, data, attr, context):
        value = await super().dump(data, attr, context)
        if value == OPTIONAL:
            return value
        return await self.schema.dump(value, context)


class List(Field):
    def __init__(
            self,
            schema: Type['Schema'] = None,
            dump_to=None,
            load_from=None,
    ):
        self.schema = schema
        super().__init__(dump_to=dump_to, load_from=load_from)

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
            await self.schema.load(item, context) if self.schema else item
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
