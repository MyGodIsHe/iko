import base64

import pytest

import iko


CONTEXT = {'private_offset': 1}


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


class Age(iko.Field):
    OPTIONAL_LIST = (None, iko.OPTIONAL)


class Named(iko.Schema):
    name = iko.Field()


class HumanSchema(Named):
    gender = iko.Field()
    secret = PrivateField()


class Pet(iko.Schema):
    owner = iko.Nested(HumanSchema)
    friends = iko.List(HumanSchema)
    age = Age(default=0)


class CatSchema(Named, Pet):
    _id = iko.Field(outer_name='id')
    skip = iko.Field()


@pytest.mark.parametrize(
    'data, expected',
    [
        pytest.param(
            {
                '_id': '42',
                'name': 'Jake',
                'age': 100,
                'owner': {
                    'name': 'Ilya',
                    'gender': 'male',
                    'secret': 'bnBwbw=='
                },
                'friends': [
                    {
                        'name': 'Pauline',
                        'gender': 'female'
                    },
                    {
                        'name': 'Harry',
                        'gender': 'male'
                    }
                ]
            },
            {
                'id': '42',
                'name': 'Jake',
                'age': 100,
                'owner': {
                    'name': 'Ilya',
                    'gender': 'male',
                    'secret': 'moon'
                },
                'friends': [
                    {
                        'name': 'Pauline',
                        'gender': 'female'
                    },
                    {
                        'name': 'Harry',
                        'gender': 'male'
                    }
                ]
            },
            id='base'
        ),
        pytest.param(
            {},
            {
                'age': 0,
            },
            id='default'
        ),
        pytest.param(
            {
                'age': None,
            },
            {},
            id='optional'
        ),
    ]
)
async def test_dump(data, expected):
    assert await CatSchema.dump(data, context=CONTEXT) == expected
    assert await CatSchema.dump_many([data], context=CONTEXT) == [expected]


@pytest.mark.parametrize(
    'data, expected',
    [
        pytest.param(
            {
                'id': '42',
                'name': 'Jake',
                'age': 100,
                'owner': {
                    'name': 'Ilya',
                    'gender': 'male',
                    'secret': 'moon'
                },
                'friends': [
                    {
                        'name': 'Pauline',
                        'gender': 'female'
                    },
                    {
                        'name': 'Harry',
                        'gender': 'male'
                    }
                ]
            },
            {
                '_id': '42',
                'name': 'Jake',
                'age': 100,
                'owner': {
                    'name': 'Ilya',
                    'gender': 'male',
                    'secret': 'bnBwbw=='
                },
                'friends': [
                    {
                        'name': 'Pauline',
                        'gender': 'female'
                    },
                    {
                        'name': 'Harry',
                        'gender': 'male'
                    }
                ]
            },
            id='base',
        ),
        pytest.param(
            {},
            {
                'age': 0,
            },
            id='default',
        ),
        pytest.param(
            {
                'age': None,
            },
            {},
            id='optional',
        )
    ]
)
async def test_load(data, expected):
    assert await CatSchema.load(data, context=CONTEXT) == expected
    assert await CatSchema.load_many([data], context=CONTEXT) == [expected]


@pytest.mark.parametrize(
    'data, expected',
    [
        (
            {},
            {
                'age': 0,
            }
        )
    ]
)
async def test_empty_context(data, expected):
    assert await CatSchema.dump(data) == expected
    assert await CatSchema.dump_many([data]) == [expected]
    assert await CatSchema.load(data) == expected
    assert await CatSchema.load_many([data]) == [expected]
