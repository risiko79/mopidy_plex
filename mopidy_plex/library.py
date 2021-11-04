# -*- coding: utf-8 -*-

import logging

from mopidy import backend
from mopidy.models import SearchResult, Ref, Image

from plexapi import audio as plexaudio
from plexapi.library import MusicSection

from mopidy_plex import logger
from .cache import *

logger = logging.getLogger(__name__)

class PlexLibraryProvider(backend.LibraryProvider):
    root_directory = Ref.directory(uri='plex:directory', name='Plex Music')

    def __init__(self, *args, **kwargs):
        super(PlexLibraryProvider, self).__init__(*args, **kwargs)
        self._root = []
        self._root.append(Ref.directory(uri='plex:album', name='Albums'))
        self._root.append(Ref.directory(uri='plex:artist', name='Artists'))        

    def _item_ref(self, item, item_type):
        if item_type == 'track':
            _ref = Ref.track
        else:
            _ref = Ref.directory        
        return _ref(uri=self.backend.plex_uri(item.key, 'plex:{}'.format(item_type)),
                    name=item.title)
    
    @cache(CACHING_TIME)
    def browse(self, uri):
        logger.debug('browse: %s', str(uri))
        if not uri:
            return []
        if uri == self.root_directory.uri:
            return self._root
        parts = uri.split(':')

        # albums
        if uri == 'plex:album':
            logger.debug('self._browse_albums()')
            sections = self.backend.plexsrv.library.sections()
            albums = []
            for s in sections:
                if isinstance(s, MusicSection):
                    for a in s.albums():
                        albums.append(self._item_ref(a, 'album'))
            return albums
                      

        # a single album
        # uri == 'plex:album:album_id'
        if (len(parts) == 3 and parts[1] == 'album'):
            logger.debug('self._browse_album(uri)')
            album_id = parts[2]
            plex_uri = '/library/metadata/{}/children'.format(album_id)
            items = self.backend.plexsrv.library.fetchItems(plex_uri, cls=plexaudio.Track)
            return [self._item_ref(item, 'track') for item in items]

        # artists
        if uri == 'plex:artist':
            logger.debug('self._browse_artists()')
            sections = self.backend.plexsrv.library.sections()
            artists = []
            for s in sections:
                if isinstance(s, MusicSection):
                    for a in s.searchArtists():
                        artists.append(self._item_ref(a, 'artist'))
            return artists

        # a single artist
        # uri == 'plex:artist:artist_id'
        if len(parts) == 3 and parts[1] == 'artist':
            logger.debug('self._browse_artist(uri)')
            artist_id = parts[2]
            # get albums and tracks
            plex_uri = '/library/metadata/{}/children'.format(artist_id)
            albums = self.backend.plexsrv.library.fetchItems(plex_uri,cls=plexaudio.Track)
            ret = []
            for item in albums:
                ret.append(self._item_ref(item, 'album'))

            plex_uri = '/library/metadata/{}/allLeaves'.format(artist_id)
            tracks = self.backend.plexsrv.library.fetchItems(plex_uri,cls=plexaudio.Track)
            for item in tracks:
                ret.append(self._item_ref(item, 'track'))
            return ret

        # all tracks of a single artist
        # uri == 'plex:artist:artist_id:all'
        if len(parts) == 4 and parts[1] == 'artist' and parts[3] == 'all':
            logger.debug('self._browse_artist_all_tracks(uri)')
            artist_id = parts[2]
            plex_uri = '/library/metadata/{}/allLeaves'.format(artist_id)
            tracks = self.backend.plexsrv.library.fetchItems(plex_uri,cls=plexaudio.Track)
            ret = []
            for item in tracks:
                ret.append(self._item_ref(item, 'track'))
            return ret

        logger.debug('Unknown uri for browse request: %s', uri)
        return []    

    @cache(CACHING_TIME)
    def lookup(self, uri):
        '''Lookup the given URIs.
        Return type:
        list of mopidy.models.Track '''

        logger.debug("Lookup Plex uri '%s'", uri)

        parts = uri.split(':')
        item_id = parts[2]

        if uri.startswith('plex:artist:'):
            # get all tracks for artist            
            plex_uri = '/library/metadata/{}/allLeaves'.format(item_id)
        elif uri.startswith('plex:album:'):
            # get all tracks for album
            plex_uri = '/library/metadata/{}/children'.format(item_id)
        elif uri.startswith('plex:track:'):
            # get track
            plex_uri = '/library/metadata/{}'.format(item_id)

        tracks = []
        for item in self.backend.plexsrv.library.fetchItems(plex_uri, cls=plexaudio.Track):  
            tracks.append(self.backend.wrap_track(item, True))
        return tracks

    
    def get_images(self, uris):
        '''Lookup the images for the given URIs

        Backends can use this to return image URIs for any URI they know about be it tracks, albums, playlists... The lookup result is a dictionary mapping the provided URIs to lists of images.

        Unknown URIs or URIs the corresponding backend couldn’t find anything for will simply return an empty list for that URI.

        Parameters: uris (list of string) – list of URIs to find images for
        Return type:    {uri: tuple of mopidy.models.Image}'''
        if not isinstance(uris, list):
            uris = [uris]
        logger.debug("get_images for %s",uris)
        results = {}
        for uri in uris:
            image = self._get_image(uri)
            results.update(dict.fromkeys(uris,image))

    @cache(CACHING_TIME)
    def _get_image(self, uri):
        parts = uri.split(':')
        images = []
        if uri.startswith('plex:track:'):
            # get track
            item_id = parts[2]
            plex_uri = '/library/metadata/{}'.format(item_id)            
            for item in self.backend.plexsrv.library.fetchItems(plex_uri,cls=plexaudio.Track):                      
                images.append(Image(uri = item.thumbUrl))
        return images

    def search(self, query=None, uris=None, exact=False):
        '''Search the library for tracks where field contains values.

        Parameters:
        query (dict) – one or more queries to search for - the dict's keys being:
              {
                  'any': *, # this is what we get without explicit modifiers
                  'albumartist': *,
                  'date': *,
                  'track_name': *,
                  'track_number': *,
              }


        uris (list of string or None) – zero or more URI roots to limit the search to
        exact (bool) – if the search should use exact matching

        Returns mopidy.models.SearchResult, which has these properties
            uri (string) – search result URI
            tracks (list of Track elements) – matching tracks
            artists (list of Artist elements) – matching artists
            albums (list of Album elements) – matching albums
        '''

        # handle only searching (queries with 'any') not browsing!
        if not (query and "any" in query):
            return None

        search_query = " ".join(query["any"])
        logger.debug('Searching Plex for query "%s"', search_query)
        return self._search(search_query)

    @cache(CACHING_TIME)
    def _search(self,search_query):

        artists = []
        tracks = []
        albums = []

        for hit in self.backend.plexsrv.search(search_query):
            logger.debug('Got plex hit from query "%s": %s', search_query, hit)
            if isinstance(hit, plexaudio.Artist): artists.append(self.backend.wrap_artist(hit))
            elif isinstance(hit, plexaudio.Track): tracks.append(self.backend.wrap_track(hit))
            elif isinstance(hit, plexaudio.Album): albums.append(self.backend.wrap_album(hit))

        logger.debug("Got results: %s, %s, %s", artists, tracks, albums)

        return SearchResult(
            uri="plex:search",
            tracks=tracks,
            artists=artists,
            albums=albums
        )
    