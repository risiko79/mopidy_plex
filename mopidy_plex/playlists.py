# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

from mopidy import backend
from mopidy.models import Ref, Playlist

from mopidy_plex import logger
from .cache import *


class PlexPlaylistsProvider(backend.PlaylistsProvider):    

    @cache(CACHING_TIME)
    def as_list(self):
        '''Get a list of the currently available playlists.

        Returns a list of `mopidy.models.Ref` objects referring to the playlists.
        In other words, no information about the playlists’ content is given.'''
        logger.debug('Playlist: as_list')
        lists = self.backend.plexsrv.playlists()
        audiolists = [l for l in lists if l.playlistType == 'audio']
        return [Ref(uri='plex:playlist:{}'.format(playlist.ratingKey), 
                    name=playlist.title)
                for playlist in audiolists]

    @cache(CACHING_TIME)
    def lookup(self, uri):
        '''Lookup playlist with given URI in both the set of playlists and in any other playlist source.

        Returns the playlists or None if not found.


          Parameters:	uri (string) – playlist URI
          Return type:	mopidy.models.Playlist or None

        '''
        logger.debug('Playlist: lookup %r', uri)
        _rx = re.compile(r'plex:playlist:(?P<plid>\d+)').match(uri)
        if _rx is None:
            return None
        list_id = _rx.group('plid')
        plex_uri = '/playlists/{:s}'.format(list_id)
        plexlist = self.backend.plexsrv.library.fetchItem(plex_uri)

        PL = Playlist(
            uri=uri,
            name=plexlist.title,
            tracks=[self.backend.wrap_track(_t) for _t in plexlist.items()],
            last_modified=None, # TODO: find this value
            )
        return PL
