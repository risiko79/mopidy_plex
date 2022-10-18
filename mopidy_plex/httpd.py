from os import stat
import re
import threading
import logging
from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from .settings import settings
from .utils import *
from .helper import MopidyPlexHelper as MPH
from .subscriber import SubScribers

logger = logging.getLogger(__name__)

class PlexClientRequestHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, format, *args):
        '''
        overriding to avoid base log
        '''
        pass

    def do_HEAD(self):
        logger.debug( "Serving HEAD request..." )
        try:
            self.answer_request()
        except Exception:
            logger.exception("")

    def do_POST(self):
        logger.debug( "Serving POST request..." )
        try:
            self.answer_request()
        except Exception:
            logger.exception("")

    def do_GET(self):
        #logger.debug( "Serving GET request... %s" % self.raw_requestline)
        try:
            self.answer_request()
        except Exception:
            logger.exception("")
            self.response("",code= HTTPStatus.INTERNAL_SERVER_ERROR) #500 Internal Server Error

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Content-Length', '0')
        self.send_header('X-Plex-Client-Identifier', getIdentifier())
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Connection', 'close')
        self.send_header('Access-Control-Max-Age', '1209600')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE, PUT, HEAD')
        self.send_header('Access-Control-Allow-Headers', 'x-plex-version, x-plex-platform-version, x-plex-username, x-plex-client-identifier, x-plex-target-client-identifier, x-plex-device-name, x-plex-platform, x-plex-product, accept, x-plex-device')
        self.end_headers()
        self.wfile.close()

    def _getPlayerCapabilities(self):
        resp = getXMLHeader()
        h = MPH.get().headers
         
        resp += '<MediaContainer size="1">'
        resp += '<Player'
        resp += ' title="%s"' % getName(h)
        resp += ' protocol="plex"'
        resp += ' protocolVersion="1"'
        resp += ' protocolCapabilities="timeline,playback,playqueues,playqueues-creation"'
        #resp += ' protocolCapabilities="timeline,playback,mirror,playqueues,playqueues-creation"'
        resp += ' machineIdentifier="%s"' % getIdentifier(h)
        resp += ' product="%s"' % getProduct(h)
        resp += ' platform="%s"' % getPlatform(h)
        resp += ' platformVersion="%s"' % getVersion(h)
        resp += ' deviceClass="stb"'
        resp += ' version="1"'
        resp += "/>"
        resp += "</MediaContainer>"
        return resp    

    def response(self, body:str, code = HTTPStatus.OK, headers = {}):
        try:
            self.send_response(code)
            h = MPH.get().headers
            h.update(headers)
            for key in h:
                self.send_header(key, h[key])
            if len(body):
                self.send_header('Access-Control-Allow-Origin','*')
                self.send_header('Content-Type', 'text/xml; charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.send_header("Date",self.date_time_string())
            self.send_header('Connection', "close")
            self.end_headers()
            self.wfile.write(body.encode('latin-1', 'strict'))
        except:
            logger.exception("sending response failed")

    def _handleResult(self, result):
        if result:
            self.response(getOKMsg())
        else:
            self.response("",code=HTTPStatus.INTERNAL_SERVER_ERROR) #500 Internal Server Error
        

    def answer_request(self):
        request_path=self.path[1:]
        request_path=re.sub(r"\?.*","",request_path)
        url = urlparse(self.path)
        paramarrays = parse_qs(url.query)
        params = {}        
        for key in paramarrays:
            params[key] = paramarrays[key][0]

        if not '/poll' in request_path:
            logger.debug("request from %s is: [%s] with params %s" % (self.client_address[0], request_path, params))

        params_org = params.copy()
        params.update(self.headers)

        commandID = params.get('commandID', None)
        if commandID:
            SubScribers.get().updateCommandID(params, commandID)

        if request_path=="version":
            self.response(getVersion(MPH.get().headers))
        elif request_path=="verify":
            self.response(getOKMsg())
        elif request_path == "resources":
            resp = self._getPlayerCapabilities()
            self.response(resp, headers={'Cache-Control':'private, no-cache, no-store, must-revalidate'})
        elif "/subscribe" in request_path:
            params['host'] = self.client_address[0]
            self.response(getOKMsg())
            SubScribers.get().add(params)                
        elif "/poll" in request_path:            
            params['commandID'] = commandID
            wait = params.get('wait', 0)                       
            h = {'Access-Control-Expose-Headers':'X-Plex-Client-Identifier'}
            if wait:
                timeline = SubScribers.get().createTimeline(commandID)
                if settings.get('debug_poll',False):
                    logger.debug("poll response: %s" % timeline)
                self.response(timeline, headers=h)              
            else:
                self.response(getOKMsg(),headers=h)
        elif "/unsubscribe" in request_path:
            self.response(getOKMsg())            
            SubScribers.get().remove(params)
        elif "/playMedia" in request_path:
            self._handleResult(MPH.get().playMedia(params))
        elif request_path == "player/playback/play":
            self._handleResult(MPH.get().resume(params))
        elif request_path == "player/playback/pause":
            self._handleResult(MPH.get().pause(params))
        elif request_path == "player/playback/stop":
            self._handleResult(MPH.get().stop(params))
        elif request_path == "player/playback/stepForward":
            params['relative'] = 1*1000
            self._handleResult(MPH.get().seek(params))
        elif request_path == "player/playback/stepBack":
            params['relative'] = -1*1000
            self._handleResult(MPH.get().seek(params))
        elif request_path == "player/playback/seekTo":
            self._handleResult(MPH.get().seek(params))
        elif request_path == "player/playback/setParameters":
            self._handleResult(MPH.get().set(params))
        elif request_path == "player/playback/skipNext":
            params['direction'] = 1
            self._handleResult(MPH.get().skip(params))
        elif request_path == "player/playback/skipPrevious":
            params['direction'] = -1
            self._handleResult(MPH.get().skip(params))
        elif request_path == "player/playback/skipTo":
            self._handleResult(MPH.get().skipTo(params))
        else:
            logger.warning("unknown request: %s %s" % (request_path, params_org))
            self.response("",code=HTTPStatus.NOT_IMPLEMENTED) # 501 Not Implemented (en-US)            
        
        
        '''
        elif request_path == "player/playback/play":
            self.response(geRequestHandlerClasstOKMsg())                
        elif request_path == "player/navigation/moveUp":
            self.response(getOKMsg())                
        elif request_path == "player/navigation/moveDown":
            self.response(getOKMsg())                
        elif request_path == "player/navigation/moveLeft":
            self.response(getOKMsg())                
        elif request_path == "player/navigation/moveRight":
            self.response(getOKMsg())                
        elif request_path == "player/navigation/select":
            self.response(getOKMsg())                
        elif request_path == "player/navigation/home":
            self.response(getOKMsg())                
        elif request_path == "player/navigation/back":
            self.response(getOKMsg())
        elif request_path == "player/playback/refreshPlayQueue":
            self.response(getOKMsg())
        '''

class PlexClientHTTPServer(ThreadingHTTPServer):
    '''
    Threaded HTTP Server for remote control
    '''
    _subScribers:SubScribers = None

    def __init__(self):
        con = (settings['host'], settings['port'])
        logger.debug("init with %s " % str(con))
        SubScribers.create()
        super().__init__(con, PlexClientRequestHandler)

    def start(self):
        self._httpd_t = threading.Thread(target=self.serve_forever,args=(0.5,))
        self._httpd_t.setDaemon(True)
        self._httpd_t.start()
        SubScribers.get().start()

    def stop(self):
        SubScribers.get().stop()
        self.shutdown()
        self._httpd_t.join()
        del self._httpd_t
        