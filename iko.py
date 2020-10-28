import asyncio
import inspect
import typing

OPTIONAL = object()
EXCLUDE = 'exclude'
INCLUDE = 'include'

_TField = typing.Union['Field', typing.Type['Field']]
_TFields = typing.Dict[str, _TField]
_TSchema = typing.Union['Schema', typing.Type['Schema']]


class Field:
    OPTIONAL_LIST: typing.Iterable = (OPTIONAL,)

    def __init__(
            self,
            default=OPTIONAL,
            dump_to=None,
            load_from=None,
            outer_name=None,
    ):
        if outer_name is not None:
            assert dump_to is None and load_from is None
        self._default = default
        self.dump_to = dump_to or outer_name
        self.load_from = load_from or outer_name

    @property
    def default(self):
        if callable(self._default):
            return self._default()
        return self._default

    async def dump(self, data, attr, context):
        value = data.get(attr, self.default)
        if value in self.OPTIONAL_LIST:
            return OPTIONAL
        return await self.post_dump(value, context)

    async def post_dump(self, value, context):
        return value

    async def load(self, data, attr, context):
        value = data.get(attr, self.default)
        if value in self.OPTIONAL_LIST:
            return OPTIONAL
        return await self.post_load(value, context)

    async def post_load(self, value, context):
        return value


class Nested(Field):
    schema: 'Schema'

    def __init__(
            self,
            schema,
            default=OPTIONAL,
            dump_to=None,
            load_from=None,
            outer_name=None,
    ):
        if inspect.isclass(schema):
            self.schema = schema()
        else:
            self.schema = schema
        super().__init__(default, dump_to, load_from, outer_name)

    async def post_dump(self, value, context):
        return await self.schema.dump(value, context=context)

    async def post_load(self, value, context):
        return await self.schema.load(value, context=context)


class List(Field):
    """
    If a field is passed, then only post methods are used.
    """

    def __init__(
            self,
            schema: typing.Optional[_TSchema] = None,
            field: typing.Optional[_TField] = None,
            default=OPTIONAL,
            dump_to=None,
            load_from=None,
            outer_name=None,
    ):
        assert not (schema and field)
        self.obj_dump = None
        self.obj_load = None
        if schema:
            if inspect.isclass(schema):
                schema = schema()  # type: ignore
            self.obj_dump = schema.dump
            self.obj_load = schema.load
        if field:
            if inspect.isclass(field):
                field = field()  # type: ignore
            self.obj_dump = field.post_dump  # type: ignore
            self.obj_load = field.post_load  # type: ignore
        super().__init__(default, dump_to, load_from, outer_name)

    async def post_dump(self, value, context):
        return [
            (
                await self.obj_dump(item, context=context)
                if self.obj_dump
                else item
            )
            for item in value
        ]

    async def post_load(self, value, context):
        return [
            (
                await self.obj_load(item, context=context)
                if self.obj_load
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
        for key, field in attrs.items():
            if isinstance(field, Field):
                fields[key] = field
            elif (
                inspect.isclass(field)
                and issubclass(field, Field)
                and field.__name__ != key
            ):
                fields[key] = field()
        attrs['__fields__'] = fields
        klass = super().__new__(mcs, name, bases, attrs)

        meta = getattr(klass, 'Meta')
        klass.__opts__ = klass.OPTIONS_CLASS(meta)
        return klass


class SchemaOpts:
    def __init__(self, meta):
        self.unknown = getattr(meta, 'unknown', EXCLUDE)
        self.exclude = getattr(meta, 'exclude', tuple())


class Schema(metaclass=SchemaMeta):
    OPTIONS_CLASS = SchemaOpts

    __fields__: typing.Dict[str, Field]
    __opts__: SchemaOpts

    class Meta:
        pass

    @classmethod
    async def dump(cls, data, *, only=None, exclude=None, context=None):
        if context is None:
            context = {}

        data = await cls.pre_dump(data, context)

        only = only or cls.__fields__
        exclude = exclude or []
        exclude.extend(cls.__opts__.exclude)

        partial = set(cls.__fields__) & set(only) - set(exclude)
        fields = [
            (attr, field)
            for attr, field in cls.__fields__.items()
            if attr in partial
        ]
        fields_coros = [
            field.dump(data, attr, context) for attr, field in fields
        ]
        values = await cls.gather(fields_coros, context)
        attrs = [field.dump_to or attr for attr, field in fields]
        result = {
            attr: value
            for attr, value in zip(attrs, values)
            if value != OPTIONAL
        }
        if cls.__opts__.unknown == INCLUDE:
            known_fields = set(cls.__fields__) | set(exclude)
            result.update(
                {
                    key: value
                    for key, value in data.items()
                    if key not in known_fields
                },
            )
        return await cls.post_dump(result, context)

    @classmethod
    async def gather(cls, fields: typing.List[typing.Coroutine], context):
        return await asyncio.gather(*fields)

    @classmethod
    async def pre_dump(cls, value, context):
        return value

    @classmethod
    async def post_dump(cls, value, context):
        return value

    @classmethod
    def dump_many(cls, items, *, context=None):
        if context is None:
            context = {}
        return asyncio.gather(
            *[cls.dump(item, context=context) for item in items],
        )

    @classmethod
    async def load(cls, data, *, only=None, exclude=None, context=None):
        if context is None:
            context = {}

        data = await cls.pre_load(data, context)

        only = only or cls.__fields__
        exclude = exclude or []
        exclude.extend(cls.__opts__.exclude)

        partial = set(cls.__fields__) & set(only) - set(exclude)
        fields = [
            (attr, field)
            for attr, field in cls.__fields__.items()
            if attr in partial
        ]
        fields_coros = [
            field.load(
                data, field.load_from if field.load_from else attr, context,
            )
            for attr, field in fields
        ]
        values = await cls.gather(fields_coros, context)
        result = {
            attr: value
            for attr, value in zip([field[0] for field in fields], values)
            if value != OPTIONAL
        }
        if cls.__opts__.unknown == INCLUDE:
            known_fields = {
                field.load_from if field.load_from else attr
                for attr, field in cls.__fields__.items()
            } | set(exclude)
            result.update(
                {
                    key: value
                    for key, value in data.items()
                    if key not in known_fields
                },
            )
        return await cls.post_load(result, context)

    @classmethod
    async def pre_load(cls, value, context):
        return value

    @classmethod
    async def post_load(cls, value, context):
        return value

    @classmethod
    def load_many(cls, items, *, context=None):
        if context is None:
            context = {}
        return asyncio.gather(
            *[cls.load(item, context=context) for item in items],
        )


def schema_from_dict(*args: _TFields, **fields: _TField):
    all_fields: _TFields = {}
    for arg in args:
        all_fields.update(arg)
    all_fields.update(fields)
    return typing.cast(
        typing.Type[Schema], type('DictSchema', (Schema,), all_fields),
    )
