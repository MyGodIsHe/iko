import pytest

import iko


class Human(iko.Schema):
    name = iko.Field()
    gender = iko.Field()


class CatSchema(iko.Schema):
    _id = iko.Field(outer_name='id')
    nickname = iko.Field()
    age = iko.Field(default='infinity')
    owner = iko.Nested(Human)
    friends = iko.List(Human)
    skip = iko.Field()


@pytest.mark.parametrize(
    'data, expected',
    [
        (
            {
                '_id': '42',
                'nickname': 'Jake',
                'owner': {
                    'name': 'Ilya',
                    'gender': 'male'
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
                'nickname': 'Jake',
                'age': 'infinity',
                'owner': {
                    'name': 'Ilya',
                    'gender': 'male'
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
            }
        )
    ]
)
async def test_dump(data, expected):
    assert await CatSchema.dump(data) == expected


@pytest.mark.parametrize(
    'data, expected',
    [
        (
            {
                'id': '42',
                'nickname': 'Jake',
                'owner': {
                    'name': 'Ilya',
                    'gender': 'male'
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
                'nickname': 'Jake',
                'age': 'infinity',
                'owner': {
                    'name': 'Ilya',
                    'gender': 'male'
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
            }
        )
    ]
)
async def test_load(data, expected):
    assert await CatSchema.load(data) == expected
