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
        schema['token'] = config.Secret()
        return schema

    def setup(self, registry):
        from .backend import PlexBackend
        registry.add('backend', PlexBackend)