import logging
import pkg_resources
import os

from mopidy import config, ext

__version__ = pkg_resources.get_distribution("Mopidy-Plex").version

logger = logging.getLogger(__name__)

class Extension(ext.Extension):

    dist_name = 'Mopidy-Plex'
    ext_name = 'plex'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)
        
    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['server'] = config.String()
        schema['token'] = config.Secret(optional=True)
        schema['username'] = config.String(optional=True)
        schema['password'] = config.Secret(optional=True)
        schema['profile'] = config.String(optional=True)

        #frontend config        
        schema["port"] = config.Port(optional=True)
        schema["host"] = config.Hostname(optional=True)        
        return schema

    def setup(self, registry):
        logger.debug('setup plex backend and frontend')
        from .settings import settings
        settings['version'] = self.version
        settings['product'] = self.dist_name

        from .backend import PlexBackend
        registry.add('backend', PlexBackend)

        from .frontend import PlexFrontend
        registry.add("frontend", PlexFrontend)