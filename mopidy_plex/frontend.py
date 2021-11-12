import logging
import pykka
from mopidy.core import CoreListener

import mopidy_plex
from .register import PlexRegister
from .httpd import PlexClientHTTPServer
from .settings import settings
from .helper import MopidyPlexHelper as MPH

logger = logging.getLogger(__name__)

class PlexFrontend(pykka.ThreadingActor, CoreListener):

    def __init__(self, config, core):
        super().__init__()

        myconfig = config[mopidy_plex.Extension.ext_name]
        for key in myconfig:
            if key in settings:
                if myconfig[key] is not None:
                    settings[key] = myconfig[key]

        MPH.get().set_mopidy_core(core)

        self._reg = PlexRegister()
        self._httpd = PlexClientHTTPServer()

    def on_start(self):        
        self._reg.start()
        self._httpd.start()
        pass

    def on_stop(self):
        self._reg.stop()
        self._httpd.stop()

    def on_event(self, event, **kwargs):
        logger.debug('event: %s' % str(event))