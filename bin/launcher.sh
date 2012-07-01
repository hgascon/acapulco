#!/bin/sh

# Acapulco for the Honeynet Project 
# launcher script
# 

SPLUNK_HOME=/Applications/splunk
APP_BIN_DIR=$SPLUNK_HOME/etc/apps/Acapulco4HNP/bin
APP_LOCAL_DIR=$SPLUNK_HOME/etc/apps/Acapulco4HNP/local
SCRIPT=$APP_BIN_DIR/spl_feed2file.py
PIDFILE=$APP_BIN_DIR/spl_feed2file.py.pid
CONFIG_FILE=hpfeeds.conf
CONF_MODTIME_FILE=$APP_BIN_DIR/.config



check_config_modified ()
{
    if [ -e $CONF_MODTIME_FILE ]
    then
        current_config_modtime=$(stat -f '%m' $APP_LOCAL_DIR/$CONFIG_FILE)
        last_config_modtime=$(cat $CONF_MODTIME_FILE)
        
        if [ $current_config_modtime -eq $last_config_modtime ]
        then
            # config not modified
            return 1
        else
            # config modified
            # Store new modification time and return
            echo $current_config_modtime > $CONF_MODTIME_FILE
            return 0
            
        fi
    else
        # no .config file, so config modified (should not happen)
        # Store new modification time and return
        echo $current_config_modtime > $CONF_MODTIME_FILE
        return 0
    fi
}


# Test if the worker script is already running
#

if [ -e $PIDFILE ]
then
    pid=$(cat $PIDFILE)
    kill -0 $pid > /dev/null 2>&1
    if [ $? -eq 0 ]
    then
        # script is running
        # testing if configuration has been modified
        check_config_modified
        if [ $? -eq 0 ]
        then
            # config has been modified
            # sending SIGUSR1 to the worker, and then exit
           # echo "Configuration has been modified"
           # echo "Sending SIGUSR1 to $pid"
            kill -10 $pid
            # just wait for the worker to stop
            sleep 5
            # then save config modtime and launch it again
            echo $(stat -f '%m' $APP_LOCAL_DIR/$CONFIG_FILE) > $CONF_MODTIME_FILE
            python -O $SCRIPT &
            exit 0
        else
            # config has not been modified, nothing to do.
            exit 0
        fi
    else
        # the process is not running, but the lock file exists (a crash maybe ?)
        #
        # remove the lock file
        rm -f $PIDFILE
        # Store config file modification time
        echo $(stat -f '%m' $APP_LOCAL_DIR/$CONFIG_FILE) > $CONF_MODTIME_FILE
        # Launch the script in background and exit
        python -O $SCRIPT &
        exit 0
    fi
else
    # Store config file modification time
    echo $(stat -f '%m' $APP_LOCAL_DIR/$CONFIG_FILE) > $CONF_MODTIME_FILE
    # working script is not running. launch it
    python -O $SCRIPT &
    exit 0
    
fi
exit 0










        
    




