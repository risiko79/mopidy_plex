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

class MopidyPlexAccount(MyPlexAccount):
    
    def _headers(self, **kwargs):
        """ Returns dict containing base headers for all requests to the server. """
        headers = super()._headers()
        headers.update(kwargs)
        headers['X-Plex-Device-Name'] = settings.get('name',headers['X-Plex-Device-Name'])
        headers['X-Plex-Product'] = settings.get('product',headers['X-Plex-Product'])
        headers['X-Plex-Version'] = settings.get('version','1')
        provides = headers.get('X-Plex-Provides', "player,controller").split(',')
        if not 'player'in provides:
            provides.append('player')
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
        token=config['token']
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

        self._plexserver = None
        for dev in self._plexaccount.devices():
            if dev.name.lower() == config['server'].lower():
                self._plexserver = dev.connect()
                break        
        
        if self._plexserver is None:
            self._plexserver = PlexServer(config['server'], session=session, token=token)


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

    def getTimeline(self, commandID:int=0):
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

        if track is None:            
            return getOKMsg()

        c = ""
        c += '<MediaContainer size="3" machineIdentifier="%s" commandID="%s">' % (getIdentifier(h),commandID)
        c += '<Timeline type="video" state="stopped"/>'
        c += '<Timeline type="photo" state="stopped"/>'
        c += '</MediaContainer>'
        container:ET.Element= ET.fromstring(c)
        
        controllable="playPause,stop,volume,shuffle,repeat,skipPrevious,skipNext,stepBack,stepForward,seekTo"
        m = '<Timeline type="music" itemType="music" state="stopped" controllable="%s"/>' % controllable
        t_music:ET.Element = ET.fromstring(m)

        if state == mpc.PlaybackState.STOPPED:
            t_music.set('state','stopped')
        elif state == mpc.PlaybackState.PAUSED:
            t_music.set('state','paused')            
        elif state == mpc.PlaybackState.PLAYING:
            t_music.set('state','playing')            
        else:
            logger.error('unknown state %s', str(state))

        ratingKey = parseKey(track.uri)

        t_music.set('playbackTime', str(tpos))
        t_music.set('duration', str(track.length))                        
        t_music.set('playQueueVersion',"1")
        t_music.set('ratingKey', ratingKey)
        t_music.set('key', '/library/metadata/%s' % ratingKey)
        t_music.set('adState',"NO_VALUE")
        t_music.set('repeat', "0")
        t_music.set('offline', "NO_VALUE")
        t_music.set('protocol', self._playingInfos.get('protocol',"NO_VALUE"))
        t_music.set('bufferedTime', self._playingInfos.get('bufferedTime',"NO_VALUE"))
        t_music.set('address', self._playingInfos.get('address',"NO_VALUE"))
        t_music.set('timeToFirstFrame', self._playingInfos.get('timeToFirstFrame',"NO_VALUE"))
        t_music.set('machineIdentifier', self._playingInfos.get('machineIdentifier',"NO_VALUE"))
        t_music.set('bandwidth', self._playingInfos.get('bandwidth',"NO_VALUE"))
        t_music.set('mediaIndex', self._playingInfos.get('mediaIndex',"0"))
        t_music.set('timeStalled', self._playingInfos.get('timeStalled',"NO_VALUE"))
        t_music.set('bufferedSize', self._playingInfos.get('bufferedSize',"NO_VALUE"))
        t_music.set('url', self._playingInfos.get('url',"null"))
        t_music.set('token', self._playingInfos.get('token',"NO_VALUE"))
        t_music.set('volume', str(volume))
        t_music.set('providerIdentifier', self._playingInfos.get('machineIdentifier',"NO_VALUE"))
        t_music.set('port', self._playingInfos.get('port',"NO_VALUE"))            
        t_music.set('containerKey', self._playingInfos.get('containerKey',"NO_VALUE"))
        t_music.set('playQueueItemID', self._playingInfos.get('playQueueItemID',"NO_VALUE"))
        t_music.set('adDuration', self._playingInfos.get('adDuration',"NO_VALUE"))
        t_music.set('time', str(tpos))
        t_music.set('shuffle', self._playingInfos.get('shuffle',"0"))
        t_music.set('updated', self._playingInfos.get('updated',"NO_VALUE"))
        t_music.set('adTime', self._playingInfos.get('adTime',"NO_VALUE"))
        queue:PlexPlayQueue = self._playingInfos.get('playQueue', None)
        if queue:
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

        tlid = None        
        self._playingInfos = params.copy()
        containerKey = parseKey(params.get('containerKey',"None"))

        if containerKey is None:
            params['containerKey'] = "NO_VALUE"
        else:
            self._playingInfos['containerKey'] = '/playQueues/'+containerKey
            try:                    
                q = PlexPlayQueue.get(server = self._plexserver, playQueueID=int(containerKey))
                self._playingInfos['playQueue'] = q
                cnt = 0
                for item in q.items:
                    uris.append('plex:track:%s' % item.ratingKey)
                    cnt+=1
                    if item.ratingKey == int(sel_track_id):
                        tlid = cnt
            except:
                self._playingInfos['playQueue'] = None
        self._tracklist.clear()
        if len(uris) == 0:
            uris.append('plex:track:%s' % sel_track_id)
        self._tracklist.add(uris=uris)
        self._playback.play(tlid = tlid)
        return True        

    def resume(self, params:dict):
        self._playback.resume()
        return True

    def pause(self, params:dict):
        self._playback.pause()
        return True
        
    def stop(self, params:dict):
        self._playback.stop()
        return True

    def seek(self, params:dict):
        millis = int(params.get('offset','-1'))
        if millis < 0:
            millis = self._playback.get_time_position().get()
            millis += int(params.get('relative','0'))
        ret = self._playback.seek(millis).get()
        return ret

    def set(self, params:dict):
        volume = params.get('volume', None)
        ret = False
        if volume:        
            ret = self._mixer.set_volume(int(volume)).get()
        return ret

    def skip(self, params:dict):
        dir = params.get('direction', None)
        if dir>0:            
            self._playback.next()
        else:
            self._playback.previous()
        return True
