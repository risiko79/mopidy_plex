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

.. note:: install mopity-plex as the user running mopity


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
    profile = 

'Servername' above can be the name of the server (not the hostname and port) or it could be <hostname|ip>:port.
You can find the server name in plex web settings.
'token' is a valid registered token from your plexpass account 
If 'token' is set username and password are ignored otherwise username and password is needed to login.
'profile' is plex home user to switch after login


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


Logging/Debugging
=================

enabled logging in mopidy::

    [logging]
    config_file =<path to log configuration>/logging.conf

example logging configuration to debug mopity-plex::
    
    [loggers]
    keys = root,plex

    [handlers]
    keys = file,fileplex

    [formatters]
    keys = simple

    [logger_root]
    handlers = file

    [handler_file]
    class = handlers.RotatingFileHandler
    formatter = simple
    level = INFO
    args = ('<path>/mopidy.log','a',100000,10,)

    [handler_fileplex]
    class = handlers.RotatingFileHandler
    formatter = simple
    level = DEBUG
    args = ('<path>/mopidy_plex.log','a',100000,10,)

    [formatter_simple]
    format = %(asctime)s %(levelname)s %(name)s(%(lineno)d): %(message)s

    [logger_plex]
    level = DEBUG
    handlers = fileplex 
    qualname = mopidy_plex
    propagate = 1

