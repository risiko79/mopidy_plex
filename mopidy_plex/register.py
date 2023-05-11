
import logging
import socket
import threading
import time
import struct
from .settings import settings
from .utils import *
from .helper import MopidyPlexHelper as MPH

logger = logging.getLogger(__name__)

PLEX_GDM_IP = '239.0.0.250'     #multicast ip to Plex server(s)
PLEX_MULTICAST_PORT = 32413
PLEX_GDM_CLIENT_PORT = 32412    #gdm client port

class PlexRegister:

    def __init__(self):        
        self.multicast = (PLEX_GDM_IP, PLEX_MULTICAST_PORT)
   
        self._discovery_is_running = False
        self._registration_is_running = False

        headers = MPH.get().headers
        self.client_id = getIdentifier(headers)

        self.client_data= "Content-Type: plex/media-player\r\n"
        self.client_data+= "Name: %s\r\n" % getName(headers)     
        self.client_data+= "Port: %s\r\n" % str(settings['port'])
        self.client_data+= "Product: %s\r\n" % getProduct(headers)   
        self.client_data+= "Protocol: plex\r\n"
        self.client_data+= "Protocol-Version: 1\r\n"
        self.client_data+= "Protocol-Capabilities: timeline,playback,playqueues\r\n"
        #self.client_data+= "Protocol-Capabilities: timeline,mirror,playback,playqueues,playqueues-creation,provider-playback\r\n"
        self.client_data+= "Resource-Identifier: %s\r\n" % self.client_id
        self.client_data+= "Updated-At: %s\r\n" % int(time.time()) # 
        self.client_data+= "Version: %s\r\n" % getVersion(headers)
        self.client_data+= "Device-Class: stb\r\n"
        
        logger.debug("client data %s" % self.client_data)

    def __del__(self):
        self.stop()

    def _run_registration(self):
        update_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        
        #Set socket reuse, may not work on all OSs.
        try:
            update_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        except:
            pass
        
        #Attempt to bind to the socket to recieve and send data.  If we can;t do this, then we cannot send registration
        try:
            update_sock.bind(('0.0.0.0',PLEX_GDM_CLIENT_PORT))
        except:
            logger.exception("Unable to bind to port [%s] - client will not be registered" % PLEX_GDM_CLIENT_PORT)
            self._registration_is_running = False
            return
            
        # Set the time-to-live for messages for local network
        gdm_timeout = 1
        update_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("B", gdm_timeout))
        
        update_sock.setsockopt(
            socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(PLEX_GDM_IP) + socket.inet_aton('0.0.0.0'))
        update_sock.setblocking(False)
        
        #Send initial client registration
        try:
            #msg = "HELLO * HTTP/1.1\r\n"
            msg = "HELLO * HTTP/1.1\r\n%s" % self.client_data
            update_sock.sendto(msg.encode(encoding = 'UTF-8'), self.multicast)
        except:
            logger.exception("Unable to send registeration message")
            self._registration_is_running = False
            return
        
        #Now, listen for client discovery reguests and respond.
        while self._registration_is_running:
            addr = ""
            data = ""
            try:
                bdata, addr = update_sock.recvfrom(1024)
                data = bdata.decode('utf-8').strip()
            except Exception as ex:
                # no error
                pass

            if len(data) == 0:
                continue

            if "M-SEARCH * HTTP/1." in data:
                #logger.debug("Recieved M-SEARCH UDP packet from [%s]" % addr)
                try:
                    #msg = "HELLO * HTTP/1.1\r\n%s" % self.client_data
                    msg = "HTTP/1.1 200 OK\r\n%s" % self.client_data
                    update_sock.sendto(msg.encode(encoding = 'UTF-8'), addr)
                except Exception:
                    logger.exception("Unable to send client update message %s" % str(ex))
            else:
                logger.debug("Recieved UDP packet from [%s] containing [%s]" % (addr, data))
                time.sleep(0.5)

        logger.debug("Client Update loop stopped")
        
        #When we are finished, then send a final goodbye message to deregister cleanly.
        logger.debug("Sending registration data: BYE")
        try:
            msg = "BYE * HTTP/1.1\r\n%s" % self.client_data
            update_sock.sendto(msg.encode(encoding = 'UTF-8'),self.multicast)
        except Exception:
            logger.exception("Unable to send client update message")
        update_sock.close()                         

    def stop(self):
        if not self._registration_is_running:
            return
        logger.debug("Registration shutting down")
        self._registration_is_running = False
        self.register_t.join()
        del self.register_t
        
        
    def start(self):
        if self._registration_is_running:
            return
        logger.debug("Registration starting up")
        self._registration_is_running = True
        self.register_t = threading.Thread(target=self._run_registration)
        self.register_t.setDaemon(True)
        self.register_t.start()