****************************
Mopidy-Plex
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-Plex.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-Plex/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/Mopidy-Plex.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-Plex/
    :alt: Number of PyPI downloads

Mopidy extension for playing audio from a Plex server and make mopidy to a plex client


Installation
============

Install by running::

    pip install Mopidy-Plex

Or, if available, install the Debian/Ubuntu package from `apt.mopidy.com
<http://apt.mopidy.com/>`_.


And you need the `python-plexapi` module as well::

    pip install plexapi


Configuration
=============

Before starting Mopidy, you must add configuration for
Mopidy-Plex to your Mopidy configuration file::

    [plex]
    enabled = true
    server = Servername
    token = plex token
    username = Username
    password = Password
    port = 
    host =

Servername above can be the name of the server (not the hostname and port) or <hostname|ip>:port.
You can find the server name in plex web settings.
token is a valid an registered token from your plexpass account 
If token is set username and password are ignored otherwise username and password is needed to login.


Project resources
=================

- `Source code <https://github.com/risiko79/mopidy_plex>`_
- `Issue tracker <https://github.com/risiko79/mopidy_plex/issues>`_


Credits
=======

- Original author: `@havardgulldahl <https://github.com/havardgulldahl>`_
- Current maintainer: `@risiko79 <https://github.com/risiko79>`_
- `Contributors <https://github.com/risiko79/mopidy_plex/graphs/contributors>`_


Changelog
=========

v0.1.0 (UNRELEASED)
----------------------------------------


v0.1.0b (2016-02-02)
----------------------------------------

- Initial beta release.
- Listing and searching Plex Server content works.
- Playing audio works.


v0.1.0c (2016-06-29)
----------------------------------------

- Add support for remote Plex Servers

v0.2.0 (2022-01-03)
----------------------------------------

- ported to python 3
- ported to current python-plexapi version
- added frontend to act mopity as a plex client
- add plex-token support
