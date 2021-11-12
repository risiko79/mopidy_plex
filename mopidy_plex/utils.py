import re

def parseKey(txt:str):
    rx = re.compile(r'(.*/|.*:)(?P<track_id>\d+)')
    rm = rx.match(txt)
    id = rm.group('track_id')
    return id

def getXMLHeader():
    return '<?xml version="1.0" encoding="utf-8"?>'+"\r\n"

def getOKMsg():
    return getXMLHeader() + '<Response code="200" status="OK" />'

def getPlatform(headers:dict):
    return headers.get('X-Plex-Platform',"")

def getName(headers:dict):
    return headers.get('X-Plex-Device-Name',"")

def getIdentifier(headers:dict):
    return headers.get('X-Plex-Client-Identifier',"")

def getProduct(headers:dict):
    return headers.get('X-Plex-Product',"")

def getVersion(headers:dict):
    return headers.get('X-Plex-Version',"")    

def timeToMillis(time):
    return (time['hours']*3600 + time['minutes']*60 + time['seconds'])*1000 + time['milliseconds']

def millisToTime(t):
    millis = int(t)
    seconds = millis / 1000
    minutes = seconds / 60
    hours = minutes / 60
    seconds = seconds % 60
    minutes = minutes % 60
    millis = millis % 1000
    return {'hours':hours,'minutes':minutes,'seconds':seconds,'milliseconds':millis}

def textFromXml(element):
    return element.firstChild.data