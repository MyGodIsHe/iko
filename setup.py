from setuptools import setup

with open("README.rst", "r") as fh:
    long_description = fh.read()


setup(
    name='iko',
    description=(
        'Iko is an asynchronous micro-framework '
        'for converting data into different structures.'
    ),
    long_description=long_description,
    version='0.2.0',
    license='MIT',
    author='Ilya Chistyakov',
    author_email='ilchistyakov@gmail.com',
    py_modules=['iko'],
    zip_safe=False,
    python_requires=">=3.6",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        'Programming Language :: Python :: 3.8',
    ],
    project_urls={
        'Source': 'https://github.com/MyGodIsHe/iko',
    },
)
