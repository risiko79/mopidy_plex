from array import array
import logging

from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from plexapi.playqueue import PlayQueue as PlexPlayQueue

import mopidy.core as mpc
import mopidy.models as mpm
import mopidy.mixer as mpi

import xml.etree.ElementTree as ET
import pykka

from .settings import settings
from .utils import *

logger = logging.getLogger(__name__)
no_value = "NO_VALUE"
class MopidyPlexAccount(MyPlexAccount):
    
    def _headers(self, **kwargs):
        """ Returns dict containing base headers for all requests to the server. """
        headers = super()._headers()
        headers.update(kwargs)
        headers['X-Plex-Device-Name'] = settings.get('name',headers['X-Plex-Device-Name'])
        headers['X-Plex-Product'] = settings.get('product',headers['X-Plex-Product'])
        headers['X-Plex-Version'] = settings.get('version','1')
        provides = "client,player,pubsub-player,controller".split(',')
        headers['X-Plex-Provides'] = ','.join(provides)
        return headers 

class MopidyPlexHelper(object):

    _instance = None
    _plexaccount = None
    _mopidy_core:mpc = None
    _playingInfos:dict = {}

    def __new__(cls, config:dict=None, session=None):
        if cls._instance is None:           
            k = super(MopidyPlexHelper, cls).__new__(cls)
            k.__init__(config,session)
            cls._instance = k
        return cls._instance

    
    @classmethod
    def create(cls, config:dict, session):
        #del cls._instance
        #cls._instance = None
        return cls(config, session)

    @classmethod
    def get(cls):
        return cls._instance

    def __init__(self, config:dict=None, session=None):
        if self._instance:
            self = self._instance
            return
        if config is None:
            return
        self._core = None
        token=config.get('token', None)
        user=config.get('profile', None)
        if token is None:
            self._plexaccount = MopidyPlexAccount(
                username=config['username'],
                password=config['password'],
                session=session)
        else:
            self._plexaccount = MopidyPlexAccount(
                token=token,
                session = session
            )

        token = self._plexaccount.authenticationToken

        _plexserver = None
        self._plexserver = None
        devices = self._plexaccount.devices()
        for dev in devices:
            if not 'server' in dev.provides:
                continue
            logger.info("plex server %s found" % dev.name)
            if dev.name.lower() == config['server'].lower():
                _plexserver = dev.connect()
                break        
        
        if _plexserver is None:
            try:
                _plexserver = PlexServer(config['server'], session=session, token=token)
            except:
                logger.error("no plex server found")
                return

        self._plex_admin_server = _plexserver
        if user is not None:
            try:
                _plexserver = _plexserver.switchUser(user)
            except Exception as ex:
                logger.error("switch to user %s failed: %s",user,str(ex))
        
        self._plexserver = _plexserver
    

    @property
    def server(self):
        return self._plexserver

    @property
    def headers(self) -> dict:
        if self._plexaccount is None:
            return {}
        h = self._plexaccount._headers()
        return h

    @property
    def _playback(self) -> mpc.PlaybackController:
        return self._mopidy_core.playback # is ThreadingActor

    @property
    def _tracklist(self) -> mpc.TracklistController:
        return self._mopidy_core.tracklist # is ThreadingActor

    @property
    def _mixer(self) -> mpi.Mixer:
        return self._mopidy_core.mixer # is ThreadingActor
        

    def set_mopidy_core(self, core):
        self._mopidy_core = core

    def getTimeline(self, commandID = None):
        h = self._plexaccount._headers()

        state = mpc.PlaybackState.STOPPED   
        tpos = 0 
        track:mpm.Track = None
        volume:int = 100

        features:pykka.ThreadingFuture = self._playback.get_state().join(
                self._playback.get_time_position(),
                self._playback.get_current_track(),
                self._mixer.get_volume())
        try:
            ret = features.get(1)
            state = ret[0]
            tpos = ret[1]
            track = ret[2]
            volume = ret[3]
            if volume is None:
                volume = 100
        except:
            pass

        resp_ok = True
        if commandID is None:
            commandID = 'COMMANDID_UNKNOWN'
            resp_ok = False

        ident = getIdentifier(h)
        c = ""
        c += '<MediaContainer size="3" machineIdentifier="%s" commandID="%s">' % (ident,commandID)
        c += '<Timeline type="video" state="stopped"/>'
        c += '<Timeline type="photo" state="stopped"/>'
        c += '</MediaContainer>'
        container:ET.Element= ET.fromstring(c)
        
        controllable="playPause,stop,volume,shuffle,repeat,skipPrevious,skipNext,stepBack,stepForward,seekTo"
        m = '<Timeline type="music" itemType="music" state="stopped" controllable="%s"/>' % (controllable)
        t_music:ET.Element = ET.fromstring(m)

        if state == mpc.PlaybackState.STOPPED:
            t_music.set('state','stopped')
        elif state == mpc.PlaybackState.PAUSED:
            t_music.set('state','paused')            
        elif state == mpc.PlaybackState.PLAYING:
            t_music.set('state','playing')            
        else:
            logger.error('unknown state %s', str(state))

        ratingKey = None
        play_req_key = None
        duration = '0'

        if resp_ok and track is None:
            return getOKMsg()
        
        key = self._playingInfos.get('key',None)
        if key:
            play_req_key = parseKey(key)

        if track:
            ratingKey = parseKey(track.uri)
            duration = str(track.length)
        else:
            ratingKey = play_req_key

        if ratingKey:
            t_music.set('playbackTime', str(tpos))
            t_music.set('duration', duration)                        
            t_music.set('playQueueVersion',"1")
            t_music.set('ratingKey', ratingKey)
            t_music.set('key', '/library/metadata/%s' % ratingKey)
            t_music.set('adState',no_value)
            t_music.set('repeat', "0")
            t_music.set('offline', no_value)
            t_music.set('protocol', self._playingInfos.get('protocol',no_value))
            t_music.set('bufferedTime', self._playingInfos.get('bufferedTime',no_value))
            t_music.set('address', self._playingInfos.get('address',no_value))
            t_music.set('timeToFirstFrame', self._playingInfos.get('timeToFirstFrame',no_value))
            t_music.set('machineIdentifier', self._playingInfos.get('machineIdentifier',no_value))
            t_music.set('bandwidth', self._playingInfos.get('bandwidth',no_value))
            t_music.set('mediaIndex', self._playingInfos.get('mediaIndex',"0"))
            t_music.set('timeStalled', self._playingInfos.get('timeStalled',no_value))
            t_music.set('bufferedSize', self._playingInfos.get('bufferedSize',no_value))
            t_music.set('url', self._playingInfos.get('url',no_value))
            t_music.set('token', self._playingInfos.get('token',no_value))
            t_music.set('volume', str(volume))
            t_music.set('providerIdentifier', self._playingInfos.get('machineIdentifier',no_value))
            t_music.set('port', self._playingInfos.get('port',no_value))            
            t_music.set('containerKey', self._playingInfos.get('containerKey',no_value))
            t_music.set('playQueueItemID', self._playingInfos.get('playQueueItemID',no_value))
            tmp = self._playingInfos.get('containerKey',no_value).split('/')
            t_music.set('playQueueID', no_value)
            if len(tmp)>1:
                t_music.set('playQueueID', str(tmp[2]))
            t_music.set('adDuration', self._playingInfos.get('adDuration',no_value))
            t_music.set('time', str(tpos))
            t_music.set('shuffle', self._playingInfos.get('shuffle',"0"))
            t_music.set('updated', self._playingInfos.get('updated',no_value))
            t_music.set('adTime', self._playingInfos.get('adTime',no_value))
            t_music.set('guid', self._playingInfos.get('guid',no_value))
            queue:PlexPlayQueue = self._playingInfos.get('playQueue', None)
            if queue and ratingKey != no_value:
                for item in queue.items:
                    if item.ratingKey == int(ratingKey):
                        t_music.set('playQueueItemID', str(item.playQueueItemID))
                        break
        container.append(t_music)
        c=ET.tostring(container, encoding = 'unicode', xml_declaration=getXMLHeader())
        return c

    def playMedia(self, params:dict):        
        sel_track_id = parseKey(params['key'])
        uris = []            
        if sel_track_id is None:
            return False
      
        self._playingInfos = params.copy()
        containerKey = parseKey(params.get('containerKey',None))

        if containerKey is None:
            params['containerKey'] = no_value
        else:
            self._playingInfos['containerKey'] = '/playQueues/'+containerKey
            try:                    
                q = PlexPlayQueue.get(server = self._plexserver, playQueueID=int(containerKey))
                self._playingInfos['playQueue'] = q
                for item in q.items:
                    uris.append('plex:track:%s' % item.ratingKey)
            except:
                self._playingInfos['playQueue'] = None
        if len(uris) == 0:
            uris.append('plex:track:%s' % sel_track_id)
        
        self._refreshPlayQueue(uris)
        return self._skipTo(sel_track_id)

    def refreshPlayQueue(self, params:dict):
        playQueueID = params.get('playQueueID',None)
        uris = []
        if playQueueID is None:
            return False
        else:
            self._playingInfos['containerKey'] = '/playQueues/'+playQueueID
            q = PlexPlayQueue.get(server = self._plexserver, playQueueID=int(playQueueID))
            self._playingInfos['playQueue'] = q
            for item in q.items:
                uris.append('plex:track:%s' % item.ratingKey)
        return self._refreshPlayQueue(uris)

    def _refreshPlayQueue(self, uris:array):
        tl_tracks = self._tracklist.get_tl_tracks().get()

        # remove
        r_filter = {'uri':[]}
        for tl_track in tl_tracks:
            found = False
            for plex_uri in uris:
                if tl_track.track.uri == plex_uri:
                    found = True
                    break
            if not found:
                r_filter['uri'].append(tl_track.track.uri)

        if len(r_filter['uri']):
            self._tracklist.remove(r_filter).get()
            tl_tracks = self._tracklist.get_tl_tracks().get()
        
        # add new
        add = []
        for plex_uri in uris:
            found = False
            for tl_track in tl_tracks:                
                if tl_track.track.uri == plex_uri:
                    found = True
                    break
            if not found:
                add.append(plex_uri)
        if len(add):
            cur_tl_track = self._playback.get_current_tl_track().get()
            at_position = None
            if cur_tl_track:
                at_position = self._tracklist.index(tl_track=cur_tl_track).get()+1
            self._tracklist.add(uris=add, at_position=at_position).get()
            tl_tracks = self._tracklist.get_tl_tracks().get()
        
        assert len(tl_tracks) == len(uris)

        # sort
        for tl_track in tl_tracks:
            idx_plex = 0
            for plex_uri in uris:
                if tl_track.track.uri == plex_uri:
                    found = True
                    idx = self._tracklist.index(tl_track=tl_track).get()
                    if idx != idx_plex:
                        self._tracklist.move(idx,idx,idx_plex).get()
                    break
                idx_plex = idx_plex + 1            
        return True

    def resume(self, params:dict):
        self._playback.resume().get()
        return True

    def pause(self, params:dict):
        self._playback.pause().get()
        return True
        
    def stop(self, params:dict):
        self._playback.stop().get()
        return True

    def seek(self, params:dict):
        millis = int(params.get('offset','-1'))
        if millis < 0:
            millis = self._playback.get_time_position().get()
            millis += int(params.get('relative','0'))
        ret = self._playback.seek(millis).get()
        return ret

    def _skipTo(self,track_id):
        ret = False
        tl_tracks =  self._tracklist.get_tl_tracks().get()
        for tl_track in tl_tracks:
            if parseKey(tl_track.track.uri) == track_id:
                self._playback.play(tl_track = tl_track).get()
                ret = True
                break
        return ret

    def skipTo(self, params:dict):
        key = params.get('key',None)
        if key is None:
            return False
        sel_track_id = parseKey(key)
        return self._skipTo(sel_track_id)


    def set(self, params:dict):
        volume = params.get('volume', None)
        ret = False
        if volume:        
            ret = self._mixer.set_volume(int(volume)).get()
        return ret

    def skip(self, params:dict):
        dir = params.get('direction', None)
        if dir>0:            
            self._playback.next().get()
        else:
            self._playback.previous().get()
        return True
