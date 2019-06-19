# -*- encoding: utf-8 -
#   Modified by Archwizard56
from __future__ import unicode_literals

import re

from setuptools import find_packages, setup


def get_version(filename):
    with open(filename) as fh:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", fh.read()))
        return metadata['version']

setup(
    name='Mopidy-Plex',
    version=get_version('mopidy_plex/__init__.py'),
    url='https://github.com/Archwizard56/mopidy-plex',
    license='Apache License, Version 2.0',
    author='Håvard Gulldahl And Archwizard56',
    author_email='havard@gulldahl.no',
    description='Mopidy extension for playing audio from a Plex server',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Mopidy >= 1.0',
        'Pykka >= 1.1',
        'requests',
        'plexapi',
        'cachetools'
    ],
    entry_points={
        'mopidy.ext': [
            'plex = mopidy_plex:Extension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
