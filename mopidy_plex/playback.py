# -*- coding: utf-8 -*-

import re
import logging
from mopidy import backend
from mopidy import audio as mopidyaudio
from plexapi import audio as plexaudio
from .cache import *

logger = logging.getLogger(__name__)

class PlexPlaybackProvider(backend.PlaybackProvider):
    _plextrack:plexaudio.Track = None
    _time_offset = 0

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

        self._plextrack = self.backend.plexsrv.library.fetchItem(plex_uri,cls=plexaudio.Track)
        if self._plextrack is None:
            logger.error("track '%s' not found", item_id)
            return None
        return self._plextrack.getStreamURL()

    def change_track(self, track):  
        self._time_offset = 0
        return super().change_track(track)

    def seek(self, time_position):
        """
        Seek to a given time position.
        :param time_position: time position in milliseconds
        :type time_position: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        ret = super().seek(time_position)
        if not ret and self._plextrack:
            self._time_offset = time_position
            uri = self._plextrack.getStreamURL(offset = float(self._time_offset/1000))
            self._plextrack.updateTimeline(time=time_position,state='playing')
            self.audio.prepare_change()
            self.audio.set_uri(uri)
            ret = self.audio.start_playback().get()
        return ret

    def get_time_position(self):
        """
        Get the current time position in milliseconds.
        :rtype: int
        """        
        pos = self.audio.get_position().get()
        pos += self._time_offset
        return pos