****************************
Mopidy-Plex
****************************

Mopidy extension for playing audio from a Plex server and make mopidy to a plex client


Installation
============

Download::
    
    Download latest whl package from https://github.com/risiko79/mopidy_plex/releases/latest

Install by running::

    pip install Mopidy_Plex-<latest_version>-py3-none-any.whl


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

 - https://github.com/risiko79/mopidy_plex/releases

