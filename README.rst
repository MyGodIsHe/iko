iko
==========

.. image:: https://img.shields.io/pypi/v/iko.svg
    :target: https://pypi.org/project/iko/

.. image:: https://img.shields.io/pypi/pyversions/iko.svg
    :target: https://pypi.org/project/iko/

.. image:: https://codecov.io/gh/MyGodIsHe/iko/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/MyGodIsHe/iko
    :alt: Code coverage Status

.. image:: https://travis-ci.org/MyGodIsHe/iko.svg?branch=master
    :target: https://travis-ci.org/MyGodIsHe/iko
    
.. image:: https://img.shields.io/pypi/dm/iko.svg
    :target: https://pypi.python.org/pypi/iko


Iko is an asynchronous micro-framework for
converting data into different structures.

Inspired marshmallow_.

.. _marshmallow: https://github.com/marshmallow-code/marshmallow

Typical usage
=============

The main use-case of this framework is web service’s request and response data marshaling.

Example:

.. code-block:: python

    @swagger.schema('UserRequest', 'UserResponse')
    async def handler(request):
        body = await request.json()
        data = await UserSchema.load(body)
        await mongodb.users.insert_one(data)
        data = await mongodb.users.find_one({'_id': data['id']})
        return Response(await UserSchema.dump(data))
