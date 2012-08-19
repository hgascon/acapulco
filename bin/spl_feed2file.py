# The Honeynet Project
# Acapulco (Attack Community grAPh COnstruction) / worker hpfeeds script
# Hugo Gascon (hgascon@gmail.com)
#
# Based on Splunk for HPfeeds by Franck GUENICHOT


import os
import sys
import signal
import re
import struct
import socket
import ssl
import hashlib
import time
import datetime
import string
import json
import httplib
import urllib
from xml.etree import ElementTree

##########################################################################################################################
# Splunk Configuration
##########################################################################################################################

HOST = "localhost"
PORT = 8089
USERNAME = "admin"
PASSWORD = "admin"

##########################################################################################################################
# HPfeeds Protocol
##########################################################################################################################

OP_ERROR    = 0
OP_INFO     = 1
OP_AUTH     = 2
OP_PUBLISH  = 3
OP_SUBSCRIBE    = 4
GLASTOPF_KEYS = ["server","script","type","id"]

def log(msg):
    sys.stderr.write('[feedcli] {0}\n'.format(msg))

def msghdr(op, data):
    return struct.pack('!iB', 5+len(data), op) + data
def msgsubscribe(ident, chan):
    return msghdr(OP_SUBSCRIBE, struct.pack('!B', len(ident)) + ident + chan)
def msgauth(rand, ident, secret):
    hash = hashlib.sha1(rand+secret).digest()
    return msghdr(OP_AUTH, struct.pack('!B', len(ident)) + ident + hash)

    
class FeedUnpack(object):

    def __init__(self):
        self.buf = bytearray()

    def __iter__(self):
        return self

    def next(self):
        return self.unpack()

    def feed(self, data):
        self.buf.extend(data)

    def unpack(self):

        if len(self.buf) < 5:
            raise StopIteration('No message.')

        ml, opcode = struct.unpack('!iB', buffer(self.buf,0,5))
        if len(self.buf) < ml:
            raise StopIteration('No message.')
        
        data = bytearray(buffer(self.buf, 5, ml-5))
        del self.buf[:ml]
        return opcode, data
        
##########################################################################################################################
# Communication with Splunk
##########################################################################################################################

def spl_auth():

    # Present credentials to Splunk and retrieve the session key
    connection = httplib.HTTPSConnection(HOST, PORT)
    body = urllib.urlencode({'username':USERNAME, 'password':PASSWORD})
    headers = { 
    'Content-Type': "application/x-www-form-urlencoded", 
    'Content-Length': str(len(body)),
    'Host': HOST,
    'User-Agent': "a.py/1.0",
    'Accept': "*/*"
    }
    try:
        connection.request("POST", "/services/auth/login", body, headers)
        response = connection.getresponse()
    finally:
        connection.close()
    if response.status != 200:
        raise Exception, "%d (%s)" % (response.status, response.reason)
    body = response.read()
    sessionKey = ElementTree.XML(body).findtext("./sessionKey")

    return sessionKey

def spl_get_hpfeeds_settings():
    """
    use splunk REST api to retrieve configuration parameters
    
    """

    appname = "Acapulco4HNP"
    confname = "hpfeeds"
    stanza = "hpfeeds_settings"
    base_endpoint = "/servicesNS/admin/{0}/properties/{1}/{2}".format(appname, confname, stanza)
    keys = ("broker_host", "broker_port", "authkey_id", "authkey_secret", "channel_list", "logfilepath")
    settings_dict = {}

    sessionKey = spl_auth()
    headers = { 
    'Content-Length': "0",
    'Host': HOST,
    'User-Agent': "spl_feed2file.py/1.0",
    'Accept': "*/*",
    'Authorization': "Splunk %s" % sessionKey}

    for key in keys:
        endpoint = base_endpoint + "/{0}".format(key)
        connection = httplib.HTTPSConnection(HOST, PORT)
        try:
            connection.request("GET", endpoint, "", headers)
            response = connection.getresponse()        
        except: 
            log("(spl_get_hpfeeds_settings) Unable to connect to splunkd")
            raise
        finally:
            connection.close()
        # if response.status != 200:
        #     raise Exception, "%d (%s)" % (response.status, response.reason)
        
        value = response.read()

        # error testing: if a specific key doesn't exist
        # Splunk will return <msg type="ERROR">
        if re.search("type=\"ERROR\"", value):
            raise IOError
        
        settings_dict[key] = value
        # connection.close()
        
    # Transforms channel_list from str to list
    channel_list = []
    for c in settings_dict["channel_list"].split(','):
        channel_list.append(c)
    settings_dict["channel_list"] = channel_list
    
    return settings_dict


##########################################################################################################################
# main work
##########################################################################################################################

def handle_sigusr1(signum, frame):
    '''
    Generate an exception when a signal is received
    '''
    raise Exception("signal SIGUSR1 received")

def main():
    
    # Install an handler for SIGUSR1
    # SIGUSR1 is used to "break" the loop with an exception.
    # This is mainly used by the launcher script used in splunk
    # if the configuration has been changed the launcher will send us a SIGUSR1
    signal.signal(signal.SIGUSR1, handle_sigusr1)
    
    #Try to get our configuration from splunk first.
    try: settings = spl_get_hpfeeds_settings()
    except:
        log("Unable to get settings !")
        log("Exiting")
        return 1
    
    # Connection to HPfeeds broker. 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.settimeout(10)
    try:
        s.connect((settings["broker_host"], int(settings["broker_port"])))
    except:
        log('could not connect to broker {0}:{1}.'.format(settings["broker_host"], settings["broker_port"]))
        log('Exiting')
        return 1

        
    # Create a raw logfile output for each subscribed channel
    rawlogfiles = {}
    for c in settings["channel_list"]:
        logfilepath = settings["logfilepath"]
        logfilename = c + ".log"
        logfile = os.path.join(logfilepath, logfilename)
        outfd = open(logfile, 'a')
        rawlogfiles[c] = outfd
        
    # Modify the socket timeout to detect broken connection to broker
    #s.settimeout(300)
    # Instanciate a feed unpacker
    unpacker = FeedUnpack()
    
    # Receive first feeds
    d = s.recv(1024)

    # main working loop
    while d:
        
        unpacker.feed(d)
        for opcode, data in unpacker:
            if opcode == OP_INFO:
                rest = buffer(data, 0)
                name, rest = rest[1:1+ord(rest[0])], buffer(rest, 1+ord(rest[0]))
                rand = str(rest)

                s.send(msgauth(rand, settings["authkey_id"], settings["authkey_secret"]))
                for c in settings["channel_list"]:
                    s.send(msgsubscribe(settings["authkey_id"], c))
            elif opcode == OP_PUBLISH:
                rest = buffer(data, 0)
                ident, rest = rest[1:1+ord(rest[0])], buffer(rest, 1+ord(rest[0]))
                chan, content = rest[1:1+ord(rest[0])], buffer(rest, 1+ord(rest[0]))
                
                # What about non-json channels ?
                try: decoded = json.loads(str(content))
                except: decoded = {'raw': content}

                if isinstance(decoded, list):
                    #this is an exception for unformatted glastopf keys
                    #it can go outs
                    try:
                        decoded = dict(zip(GLASTOPF_KEYS,decoded[1:]))
                    except:
                        f = open("/Users/hgascon/acapulco_logs/err","a")
                        f.write(str(chan)+"\n")                        
                        f.write(str(decoded)+"\n")
                        f.close()
                csv = ', '.join(['{0}={1}'.format(i,j) for i,j in decoded.items()])
                outmsg = '{0} PUBLISH chan={1}, identifier={2}, {3}\n'.format(
                    datetime.datetime.now().ctime(), chan, ident, csv)
                    
                # Stores raw data in logfile    
                outfd = rawlogfiles[chan]
                print >>outfd, outmsg
                outfd.flush()
                
            elif opcode == OP_ERROR:
                log('errormessage from server: {0}'.format(data))
                break

        try:
            d = s.recv(1024)
        except KeyboardInterrupt:
            break
        except (socket.timeout, socket.error):
            log("Timeout reached on socket")
            break
        except Exception:
            break
        
    # close socket used for the communication
    # with hpfeeds broker
    s.close()
    # try to properly close log files
    try:
        for fd in rawlogfiles.values():
            fd.close()
    except:
        #ignore
        pass
    
    return 0


    
if __name__ == '__main__':
    
    pid = str(os.getpid())
    pidfile = "{0}.pid".format(sys.argv[0])
    
    # don't launch multiple instances
    if os.path.isfile(pidfile):
        print "An instance is already running !"
        sys.exit(1)
    else:
        file(pidfile, 'w').write(pid)
    
    try:
        main()
        os.unlink(pidfile)
        sys.exit(0)
    except KeyboardInterrupt:
        os.unlink(pidfile)
        sys.exit(0)

