# -*- coding: utf-8 -*-

import re
import logging
from mopidy import backend
from plexapi import audio as plexaudio
from .cache import *

logger = logging.getLogger(__name__)

class PlexPlaybackProvider(backend.PlaybackProvider):

    @cache(CACHING_TIME)
    def translate_uri(self, uri):
        '''Convert custom URI scheme to real playable URI.'''

        logger.debug("Playback.translate_uri Plex with uri '%s'", uri)

        rx = re.compile(r'plex:track:(?P<track_id>\d+)')
        rm = rx.match(uri)
        if rm is None: # uri unknown
            logger.info('Unkown uri: %s', uri)
            return None
        item_id = rm.group('track_id')
        plex_uri = '/library/metadata/{}'.format(item_id)

        plextrack = self.backend.plexsrv.library.fetchItem(plex_uri,cls=plexaudio.Track)
        if plextrack is None:
            logger.error("track '%s' not found", item_id)
            return None
        return plextrack.getStreamURL()