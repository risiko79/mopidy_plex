# -*- coding: utf-8 -*-
import re
import logging
from urllib.parse import parse_qs, urlparse
import requests
import pykka

from mopidy import backend, httpclient
from mopidy.models import  Artist, Album, Track
from requests.sessions import session



import mopidy_plex
from .library import PlexLibraryProvider
from .playback import PlexPlaybackProvider
from .playlists import PlexPlaylistsProvider
from .cache import *
from .helper import MopidyPlexHelper

logger = logging.getLogger(__name__)

def get_requests_session(proxy_config, user_agent):
    proxy = httpclient.format_proxy(proxy_config)
    full_user_agent = httpclient.format_user_agent(user_agent)

    session = requests.Session()
    session.proxies.update({'http': proxy, 'https': proxy})
    session.headers.update({'user-agent': full_user_agent})
    return session


class PlexBackend(pykka.ThreadingActor, backend.Backend):

    def __init__(self, config, audio):
        super(PlexBackend, self).__init__(audio=audio)
        self.config = config[mopidy_plex.Extension.ext_name]
        self.library = PlexLibraryProvider(backend=self)
        self.playback = PlexPlaybackProvider(audio=audio, backend=self)
        self.playlists = PlexPlaylistsProvider(backend=self)

        self.uri_schemes = ['plex', ]
        
        self.session = get_requests_session(
                  proxy_config=config['proxy'],
                  user_agent='%s/%s' % (
                      mopidy_plex.Extension.dist_name,
                      mopidy_plex.__version__))

        h = MopidyPlexHelper.create(self.config, self.session)
        self.plexsrv = h.server


    def plex_uri(self, uri_path:str, prefix='plex'):
        'Get a leaf uri and complete it to a mopidy plex uri'
        if not uri_path.startswith('/library/metadata/'):
            uri_path = '/library/metadata/' + uri_path

        if uri_path.startswith('/library/metadata/'):
            uri_path = uri_path[len('/library/metadata/'):]
        return '{}:{}'.format(prefix, uri_path)

    def resolve_uri(self, uri_path):
        'Get a leaf uri and return full address to plex server'
        if not uri_path.startswith('/library/metadata/'):
            uri_path = '/library/metadata/' + uri_path
        return self.plexsrv.url(uri_path)

    @cache(CACHING_TIME)  
    def wrap_track(self, plextrack, include_meta:bool=False):
        '''Wrap a plexapi.audio.Track to mopidy.model.track'''
        uri = self.plex_uri(plextrack.key, 'plex:track')
        
        artists = None
        album = None
        if include_meta:
            artists=[self.wrap_artist(plextrack.artist())]
            album=self.wrap_album(plextrack.album())
        
        return Track(uri=uri,
            name=plextrack.title,            
            track_no=plextrack.trackNumber,
            length = plextrack.duration,
            artists = artists,
            album = album,
            comment=plextrack.summary
            )

    @cache(CACHING_TIME)
    def wrap_artist(self, plexartist):
        '''Wrap a plex plexapi.audio.Artist result to mopidy.model.artist'''
        return Artist(uri=self.plex_uri(plexartist.key, 'plex:artist'),
                        name=plexartist.title)

    @cache(CACHING_TIME)
    def wrap_album(self,plexalbum):
        '''Wrap a plex plexapi.audio.Album to mopidy.model.album'''
        return Album(
            uri=self.plex_uri(plexalbum.key, 'plex:album'),
            name=plexalbum.title,
            artists=[self.wrap_artist(plexalbum.artist())],
            num_tracks=plexalbum.leafCount,
            num_discs=None,
            date=str(plexalbum.year)
            )


