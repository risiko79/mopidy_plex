# -*- encoding: utf-8 -*-
from setuptools import find_packages, setup

__version__ = "0.3.0"

setup(
    name='Mopidy-Plex',
    version=__version__,
    url='https://github.com/risiko79/mopidy_plex',
    project_urls={
        "Bug Tracker": "https://github.com/risiko79/mopidy_plex/issues",
    },
    license='Apache License, Version 2.0',
    author='Risiko79',
    author_email='tante_buchner@hotmail.com',
    description='Mopidy extension for playing audio from a Plex server as make mopity to a plex client',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools>=42',
        'wheel',
        'Mopidy>=3',
        'PlexAPI>=4.13',
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
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
    python_requires=">=3.8",
)
