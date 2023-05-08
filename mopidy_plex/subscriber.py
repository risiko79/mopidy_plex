import logging
import threading
import time
import xml.etree.ElementTree as ET
from http.client import *
from .helper import MopidyPlexHelper as MPH
from .utils import getXMLHeader


logger = logging.getLogger(__name__)


class SubScriber():
    def __init__(self, data:dict):
        self._data = data
        host = data.get('host',None)
        port = int(data.get('port',0))
        self._identifier = SubScriber.identifierFromParam(data)
        self._commandId = '0'

        if data.get('protocol','http') == 'http':
            self._con = HTTPConnection(host, port)
        else:
            self._con = HTTPSConnection(host, port)

    @property
    def identifier(self):
        return self._identifier

    @property 
    def cmdID(self):
        return self._commandId
    
    @cmdID.setter
    def cmdID(self, id):
        self._commandId = id

    def connect(self):
        if self._con:
            self._con.connect()

    def disconnect(self):
        if self._con:
            c = MPH.get().getTimelineContainerXML(self._commandId)
            c.set("disconnected","1")
            t = ET.tostring(c, encoding = 'unicode', xml_declaration=getXMLHeader())
            try:
                self.updateTimeline(t)
            except:
                pass
            self._con.close()

    def updateTimeline(self, timeline:str):
        headers = {
            'Content-Type': 'application/xml',
            'Access-Control-Expose-Headers':'X-Plex-Client-Identifier'}

        headers.update(MPH.get().headers)
        url = "/:/timeline"        
        self._con.request('POST', url=url, body=timeline, headers=headers)
        response:HTTPResponse = self._con.getresponse()
        data = response.read()
        #ignore response
        
    @classmethod
    def identifierFromParam(cls, data:dict):
        return data.get('X-Plex-Client-Identifier','')

class SubScribers(object):

    _instance = None
    _subscribers = {}
    _lock:threading.Lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:           
            k = super(SubScribers, cls).__new__(cls)
            k.__init__()
            cls._instance = k
        return cls._instance

    @classmethod
    def create(cls):
        #del cls._instance
        #cls._instance = None
        return cls()

    @classmethod
    def get(cls):
        return cls._instance

    def __init__(self):
        self._subscription_is_running = True
        self._sub_t = None

    def _run_subscription(self):
        while self._subscription_is_running:
            with self._lock:
                keys =  self._subscribers.keys()
                remove_c = []
                if len(keys):
                    timeline_org = MPH.get().getTimeline(None)
                    for k in keys:
                        client = self._subscribers[k]
                        
                        if client is not None:
                            timeline = timeline_org.replace('COMMANDID_UNKNOWN', client.cmdID)
                            try:
                                client.updateTimeline(timeline)
                            except:
                                logger.info("updateTimeline for subscriber %s failed - removed subscriber" % k)
                                remove_c.append(k)
                for k in remove_c:
                    client = self._subscribers[k]
                    del client
                    del self._subscribers[k]

            time.sleep(0.5)
        with self._lock:
            keys =  self._subscribers.keys()
            for k in keys:
                client = self._subscribers[k]
                client.disconnect()
                del client
            self._subscribers = {}

    def start(self):
        if self._sub_t is None:
            self._subscription_is_running = True
            self._sub_t = threading.Thread(target=self._run_subscription)
            self._sub_t.setDaemon(True)
            self._sub_t.start()

    def stop(self):
        if self._sub_t is None:
            return
        self._subscription_is_running = False
        self._sub_t.join()
        del self._sub_t
        self._sub_t = None

    def add(self, data:dict):
        identifier = SubScriber.identifierFromParam(data)
        if identifier not in self._subscribers:            
            subscriber = data.get("X-Plex-Device-Name","unknown")
            logger.info("add subscriber %s (%s)" % (subscriber,identifier))
            with self._lock:
                client = SubScriber(data)                
                try:
                    client.connect()
                    self._subscribers[client.identifier] = client
                except Exception as ex:
                    logger.error(str(ex))
        else:
            pass


    def remove(self,data:dict):
        identifier = SubScriber.identifierFromParam(data)
        if identifier not in self._subscribers:
            return
        with self._lock:
            logger.info("remove subscriber %s" % identifier)
            client = self._subscribers[identifier]
            del self._subscribers[identifier]
            if client is None:
                return
            client.disconnect()
            del client

    def updateCommandID(self, data, commandID):
        identifier = SubScriber.identifierFromParam(data)
        if identifier not in self._subscribers:
            return
        with self._lock:
            client = self._subscribers[identifier]
            if client is None:
                del self._subscribers[identifier]
                return
            client.cmdID = commandID


    