import re
from pathlib import Path

from setuptools import setup

with (Path(__file__).parent / 'aiojobs' / '__init__.py').open() as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')


long_description = open('README.rst').read() + open('CHANGES.rst').read()


setup(
    name="aiojobs",
    version=version,
    author="Andrew Svetlov",
    author_email="andrew.svetlov@gmail.com",
    long_description=long_description,
    description="Jobs scheduler for managing asyncio background tasks",
    license="Apache 2",
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Framework :: AsyncIO',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development',
        'Framework :: AsyncIO',
    ],
    url="https://github.com/aio-libs/aiojobs",
    packages=[
        'aiojobs',
    ],
    python_requires='>=3.5.3',
)
