#
# Acapulco for The Honeynet Project
# 
#
# hpfeeds_config_handler.py
# Based on Splunk for HPfeeds by Franck GUENICHOT
# This python scripts handles the parameters in the configurationp page for hpfeeds.
# It allows to modify hpfeeds.conf and makes basic parameter's validity checks.
#

import splunk.admin as admin
import splunk.entity as en
import re
import os.path
import datetime

'''
Description:    This python script handles the parameters in the configuration page for hpfeeds.
        handleList method: lists configurable parameters in the configuration page
        handleEdit method: controls the parameters and save the values in the hpfeeds.conf of local directory
                This script is mostly based on SplunkWAS application
'''

class ConfigHpfeeds(admin.MConfigHandler):
    '''
    Set up supported arguments
    '''
    def setup(self):
            if self.requestedAction == admin.ACTION_EDIT:
                    for arg in ['authkey_id', 'authkey_secret', 'broker_host', 'broker_port', 'channel_list', 'logfilepath']:
                            self.supportedArgs.addOptArg(arg)
    
    def handleList(self, confInfo):
            confDict = self.readConf("hpfeeds")
            if None != confDict:
                    for stanza, settings in confDict.items():
                            for key, val in settings.items():
                                    if key in ['authkey_id', 'authkey_secret', 'broker_host', 'broker_port', 'channel_list', 'logfilepath'] and val in [None, '']:
                                            val = ''
                                    confInfo[stanza].append(key, val)
    
    '''
    Controls parameters
    '''
    def handleEdit(self, confInfo):
        name = self.callerArgs.id
        args = self.callerArgs
        
        global boolValidAuthkeyId
        global boolValidAuthkeySecret
        global boolValidBrokerPort
        
        validAuthkeyIdPattern = re.compile(r'^[a-z0-9]{5}@hp1$')            
        validAuthkeySecretPattern = re.compile(r'[a-z0-9]{16}')
       
                    
        # Basic parameters validity checks.
        validAuthkeyId = validAuthkeyIdPattern.match(str(self.callerArgs.data['authkey_id'][0]))
        validAuthkeySecret = validAuthkeySecretPattern.match(str(self.callerArgs.data['authkey_secret'][0]))
        
        if self.callerArgs.data['broker_host'][0] in [None, '']:
            self.callerArgs.data['broker_host'][0] = ''
            boolValidBrokerHost = 0
        else:
            boolValidBrokerHost = 1
            
        if int(str(self.callerArgs.data['broker_port'][0])) > 0 and int(str(self.callerArgs.data['broker_port'][0])) <= 65535:
            boolValidBrokerPort = 1
        else:
             boolValidBrokerPort = 0
             self.callerArgs.data['broker_port'][0] = ''
        
        if validAuthkeyId or self.callerArgs.data['authkey_id'][0] in [None, '']:
            boolValidAuthkeyId = 1
        else:
            boolValidAuthkeyId = 0
            self.callerArgs.data['authkey_id'][0] = ''
        
        if validAuthkeySecret or self.callerArgs.data['authkey_secret'][0] in [None, '']:
            boolValidAuthkeySecret = 1
        else:
            boolValidAuthkeySecret = 0
            self.callerArgs.data['authkey_secret'][0] = ''
            
        if self.callerArgs.data['channel_list'][0] in [None, '']:
            self.callerArgs.data['channel_list'][0] = ''
                        
        if self.callerArgs.data['logfilepath'][0] in [None, '']:
            self.callerArgs.data['logfilepath'][0] = ''
            boolValidLogFilePath = 0
        else:
            boolValidLogFilePath = os.path.isdir(self.callerArgs.data['logfilepath'][0]) and os.access(self.callerArgs.data['logfilepath'][0], os.W_OK)
            
        
        
        
        # Writes hpfeeds configuration file.                            
        self.writeConf('hpfeeds', 'hpfeeds_settings', self.callerArgs.data)
        
        # Handles Error.
        if boolValidAuthkeyId == 0:
            raise admin.ArgValidationException, "Invalid Authkey identifier format."
        elif boolValidAuthkeySecret == 0:
            raise admin.ArgValidationException, "Invalid Authkey secret format."
        elif boolValidBrokerHost == 0:
            raise admin.ArgValidationException, "No broker host defined !"            
        elif boolValidBrokerPort == 0:
            raise admin.ArgValidationException, "Invalid broker port number !."
        elif boolValidLogFilePath == 0:
            raise admin.ArgValidationException, "Log file path doesn't exist or is not writable !"
        
        listChannel = self.callerArgs.data['channel_list'][0].split(',')             
        if listChannel in [None, '']:
            raise admin.ArgValidationException, "No channel defined !"
        
        # Now, it's time to create a proper inputs.conf in APP_DIR/local and create new indexes if needed.   

                           
        # Getting existing indexes
        try:            
            eIndexes = en.getEntities('data/indexes', sessionKey = self.getSessionKey())
        except:
            raise admin.ArgValidationException, "Error getting indexes list !"
        
        # Indexes names are defined from the channel names.
        
        
        splunkhomedirpath = os.environ.get("SPLUNK_HOME")
        splunkdbdirpath = os.environ.get("SPLUNK_DB")
        applocaldirpath = os.path.join(splunkhomedirpath, "etc", "apps", "Acapulco4HNP", "local")            
        hpfeedsdefaultdirpath = applocaldirpath.replace("local", "default")
        hpfeedsbindirpath = applocaldirpath.replace("local", "bin")
        
        broker_host = str(self.callerArgs.data['broker_host'][0])
        broker_port = str(self.callerArgs.data['broker_port'][0])
        authkey_id = str(self.callerArgs.data['authkey_id'][0])
        authkey_secret = str(self.callerArgs.data['authkey_secret'][0])
        logfilepath = str(self.callerArgs.data['logfilepath'][0])
        inputs = ""
        indexes = ""
        listNewindexes = []
        
        # Create the launcher entry in local/inputs.conf
        # Because the main working script will be out-of-the-box, an interval is set
        # to detect if the python script is still alive.
                
        inputs += "[script://./bin/launcher.sh]\n"
        inputs += "interval = 10\n"
        inputs += "disabled = false\n"
        inputs += "\n"
        
        # Create a monitor entry in local/inputs.conf for each hpfeeds channel    
        for channel in listChannel:
            index = channel
            logfilefullpath = os.path.join(logfilepath, channel + ".log")
            inputs += "[monitor://{0}]\n".format(logfilefullpath)
            inputs += "crcSalt = <SOURCE>\n"
            inputs += "sourcetype = {0}\n".format(channel)
            inputs += "source = {0}\n".format(broker_host)
            inputs += "index = {0}\n".format(index)
            inputs += "disabled = false\n"
            inputs += "\n"
            
            if not index in eIndexes.keys():
            # this index doesn't exist.  it must be created 
                if not index in listNewindexes:
                   listNewindexes.append(index)
                   indexes += "\n[{0}]\n".format(index)
                   indexes += "homePath = {0}/{1}/db\n".format(splunkdbdirpath, index)
                   indexes += "coldPath = {0}/{1}/colddb\n".format(splunkdbdirpath, index)
                   indexes += "thawedPath = {0}/{1}/thaweddb\n".format(splunkdbdirpath, index)
                   indexes += "disabled = false\n"
                   indexes += "\n"
                      
               
        # Creates inputs.conf under APP_DIR/local dir. If the file already exists, it is saved before being overwritten.    
        if not os.path.exists(os.path.join(applocaldirpath, 'inputs.conf')):
            with file(os.path.join(applocaldirpath, 'inputs.conf'),'w') as inputsDest:
                inputsDest.write(inputs)
        else:                       
            with file(os.path.join(applocaldirpath, 'inputs.conf'+datetime.datetime.now().strftime("%Y%m%dT%H%M%S")),'w') as inputsPrevConfig:
                with file(os.path.join(applocaldirpath, 'inputs.conf'),'r') as inputsTemplate:
                   config = inputsTemplate.read()
                   inputsPrevConfig.write(config)
                with file(os.path.join(applocaldirpath, 'inputs.conf'),'w') as inputsTemplate:
                    inputsTemplate.write(inputs)
                    
         # Creates indexes.conf under APP_DIR/local dir
        if len(listNewindexes) != 0:             
            with file(os.path.join(applocaldirpath, 'indexes.conf'),'a') as indexesDest:
                indexesDest.write(indexes)
           
      
        en.getEntities('data/indexes/_reload', sessionKey = self.getSessionKey())
        en.getEntities('data/inputs/monitor/_reload', sessionKey = self.getSessionKey())
    en.getEntities('data/inputs/script/_reload', sessionKey = self.getSessionKey())
        
        
# initialize the handler
admin.init(ConfigHpfeeds, admin.CONTEXT_NONE)