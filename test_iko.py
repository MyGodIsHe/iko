import base64

import iko


async def test_context():
    class PrivateField(iko.Field):
        async def post_load(self, value, context):
            value = bytes(
                (char + context['private_offset']) % 256
                for char in value.encode('utf-8')
            )
            return base64.encodebytes(value).decode('utf-8').strip()

        async def post_dump(self, value, context):
            value = bytes(
                (bt - context['private_offset']) % 256
                for bt in base64.decodebytes(value.encode('utf-8'))
            )
            return value.decode('utf-8').strip()

    class Schema(iko.Schema):
        secret = PrivateField()

    ctx = {'private_offset': 1}

    load_data = {'secret': 'moon'}
    dump_data = {'secret': 'bnBwbw=='}

    assert await Schema.load(load_data, context=ctx) == dump_data
    assert await Schema.dump(dump_data, context=ctx) == load_data


async def test_dump_to():
    class Schema(iko.Schema):
        _id = iko.Field(dump_to='id')

    assert await Schema.dump({'_id': 42}) == {'id': 42}


async def test_load_from():
    class Schema(iko.Schema):
        _id = iko.Field(load_from='id')

    assert await Schema.load({'id': 42}) == {'_id': 42}


async def test_outer_name():
    class Schema(iko.Schema):
        _id = iko.Field(outer_name='id')

    assert await Schema.dump({'_id': 42}) == {'id': 42}
    assert await Schema.load({'id': 42}) == {'_id': 42}


async def test_many():
    class Schema(iko.Schema):
        field = iko.Field

    data = {'field': '42'}

    assert await Schema.dump_many([data]) == [data]
    assert await Schema.load_many([data]) == [data]


async def test_nested():
    class Named(iko.Schema):
        name = iko.Field

    class Schema(iko.Schema):
        owner = iko.Nested(Named)
        friend = iko.Nested(Named())

    data = {
        'owner': {'name': 'Alice'},
        'friend': {'name': 'Bob'},
    }

    assert await Schema.load(data) == data
    assert await Schema.dump(data) == data


async def test_list():
    class Named(iko.Schema):
        name = iko.Field

    class Schema(iko.Schema):
        owners = iko.List(Named)
        friends = iko.List(Named())

    data = {
        'owners': [{'name': 'Alice'}, {'name': 'Bob'}],
        'friends': [{'name': 'Eve'}],
    }

    assert await Schema.load(data) == data
    assert await Schema.dump(data) == data


async def test_list_field():
    class Name(iko.Field):
        pass

    class Schema(iko.Schema):
        owners = iko.List(field=Name)
        friends = iko.List(field=Name())

    data = {
        'owners': [
            'Alice',
            'Bob',
        ],
        'friends': ['Eve'],
    }

    assert await Schema.load(data) == data
    assert await Schema.dump(data) == data


async def test_default():
    class Schema(iko.Schema):
        field42 = iko.Field(default=42)
        field43 = iko.Field(default=lambda: 43)

    expected_data = {
        'field42': 42,
        'field43': 43,
    }

    assert await Schema.dump({}) == expected_data
    assert await Schema.load({}) == expected_data


async def test_optional():
    class NullOptional(iko.Field):
        OPTIONAL_LIST = (None, iko.OPTIONAL)

    class Schema(iko.Schema):
        field = NullOptional

    assert await Schema.dump({'field': 43}) == {'field': 43}
    assert await Schema.load({'field': 43}) == {'field': 43}
    assert await Schema.dump({'field': None}) == {}
    assert await Schema.load({'field': None}) == {}


async def test_const():
    class Schema(iko.Schema):
        field = iko.Const(42)

    assert await Schema.dump({'field': 43}) == {'field': 42}
    assert await Schema.load({'field': 43}) == {'field': 42}
    assert await Schema.dump({}) == {'field': 42}
    assert await Schema.load({}) == {'field': 42}
