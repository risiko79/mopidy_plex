****************************
Mopidy-Plex
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-Plex.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-Plex/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/Mopidy-Plex.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-Plex/
    :alt: Number of PyPI downloads

.. image:: https://img.shields.io/travis/havardgulldahl/mopidy_plex/master.svg?style=flat
    :target: https://travis-ci.org/havardgulldahl/mopidy_plex
    :alt: Travis CI build status

.. image:: https://img.shields.io/coveralls/havardgulldahl/mopidy_plex/master.svg?style=flat
   :target: https://coveralls.io/r/havardgulldahl/mopidy_plex
   :alt: Test coverage

Mopidy extension for playing audio from a Plex server


Installation
============

Install by running::

    pip install Mopidy-Plex

Or, if available, install the Debian/Ubuntu package from `apt.mopidy.com
<http://apt.mopidy.com/>`_.


And you need the `python-plexapi` module as well::

    pip install plexapi


Extra setup hassle
-------------------

**Update 2016-04-14** 

Please pull  `python-plexapi`  directly from upstream at https://github.com/mjs7231/python-plexapi, which has proper Plex Audio support since https://github.com/mjs7231/python-plexapi/commit/443d1e76d8b7bc6e5181bb9791fb56b7462055e8 / March 15th.
The upcoming 2.0 release of `python-plexapi` will contain this, so get that from PyPi when it is released there.



Configuration
=============

Before starting Mopidy, you must add configuration for
Mopidy-Plex to your Mopidy configuration file::

    [plex]
    type = myplex
    enabled = true
    server = Servername
    username = Username
    password = Password
    library = Music

Servername above is the name of the server (not the hostname and port). If logged into Plex Web you can see the server name in the top left above your available libraries.

You can also use direct as type to connect directly to your server instead of authenticating through MyPlex if your server is unclaimed (not logged in)

Troubleshooting
===============

If you are having trouble with some library items, you must change the default encoding in your mopidy startup script::

    if __name__ == '__main__':
        reload(sys)
        sys.setdefaultencoding('UTF8')
        sys.exit(
            load_entry_point('Mopidy==3.0.0a1', 'console_scripts', 'mopidy')()
        )

Project resources
=================

- `Source code <https://github.com/havardgulldahl/mopidy-plex>`_
- `Issue tracker <https://github.com/havardgulldahl/mopidy-plex/issues>`_


Credits
=======

- Original author: `@havardgulldahl <https://github.com/havardgulldahl>`_
- Current maintainer: `@havardgulldahl <https://github.com/havardgulldahl>`_
- `Contributors <https://github.com/havardgulldahl/mopidy-plex/graphs/contributors>`_


Changelog
=========

v0.1.0 (UNRELEASED)
----------------------------------------


v0.1.0b (2016-02-02)
----------------------------------------

- Initial beta release.
- Listing and searching Plex Server content works.
- Playing audio works.
- Please `file bugs <https://github.com/havardgulldahl/mopidy-plex/issues>`_.


v0.1.0c (2016-06-29)
----------------------------------------

- Add support for remote Plex Servers
