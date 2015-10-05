# Acapulco (Attack Community grAPh COnstruction)

The Honeynet Project Acapulco app bundles a Splunk application that can be deployed on a central server to automatically generate meta-events from several hpfeeds channels. This events are clustered using DBSCAN or K-means algorithms and displayed at an external client using parallel coordinates graphs based on the D3.js visualization library.

## License

The Acapulco Project software is licensed under the GNU GPL license.

## Installation

You can install the Acapulco Splunk app and the visualization client in a few simple steps. Once you have downloaded the bundle, you can follow the usual Splunk instructions for installing a new application. Just unzip the file in you splunk/etc/apps directory and start Splunk to configure it.

Once that the applictaion is correctly configured and hpfeeds has done its magic, you will be able to create a new file containing all meta-events from hpfeeds log files. In order to do this, just execute the runner.py script with the logging file as input parameter. Two new files for meta-events will be created, one with plain features and a second one where the values of the features are clustered. These new events will have clusters labels as their new features values.

To deploy the visualization client, you may copy the "client" folder to the home path of you preferred web server. The needed JavaScript SDK files are already in place but you may need to install node.js if you have not done it yet.

If you don't have a running web server at hand, you can install node.js and run a simple server from the client folder:

> node sdkdo runserver

You will be able to access the client at http://localhost:6969/index.html

### Get Acapulco 

You can get the Acapulco Splunk app and the client by dowloading from GitHub, or by cloning it:

> git clone https://github.com/hgascon/Acapulco4HNP.git

### Dependencies

In order to run all the elements, you'll need to install:

1. A running Splunk server with it REST API available at the default 8089 port.
2. The Splunk JavaScript SDK [http://dev.splunk.com/view/javascript-sdk/SP-CAAAECM]
3. node.js [http://nodejs.org/]
4. Scikit-learn [http://scikit-learn.org]
5. Scipy [http://www.scipy.org/]
6. Numpy [http://numpy.scipy.org/]


## Usage


### The Splunk App

The Acapulco Splunk app is based on the HPfeeds4Splunk add-on by Frank Guenichot. It can be configured to retrieve events from different hpfeeds channels, index the events and save them in a log directory. Once that cluster runner has been call on these logs files, the app will also index the meta-events and their clustered version in two new indexes that will be available for the visualization client.

### The Cluster Runner

The cluster runner script can be run periodically from the command line:

	Usage: runner.py [options] <log dir>

	Options:  
	-h, --help            show this help message and exit  
	-o OUTPUT_TYPE, --output=OUTPUT_TYPE  
	                     Output type: csv or json (default csv)  
	-d OUTPUT_DIR, --outdir=OUTPUT_DIR  
	                     Output directory (default log dir)  
	Usage: runner.py [options] <log dir> 

Once you run it, you can expect and output similar to this:

	 $> python runner.py <your splunk logging dir>

	 [*] Processing dionaea.capture.anon.log...  
	 [*] Processing dionaea.capture.log...   
	 [*] Processing dionaea.dcerpcrequests.log...  
	 [*] Processing thug.files.log...  
	 [*] Writing output...  
	 [*] Clustering saddr...  
	 [*] Clustering sport...  
	 [*] Clustering dport...  
	 [*] Clustering daddr...  
	 [*] Clustering url...  
	 [*] Writing output...  

Files "acapulco.log" and "acapulco_plain.log" will be created in the Splunk logging directory. You can add the following line to your crontab to run the script every day and have the data updated for new events.

> 0 0 * * *  /bin/python  [...]/client/runner.py >> /var/log/acapulco_runner.log

### The D3 client

The visualization client allows to create parallel coordinate graphs from plain meta-events or their clustered version. You can use the slider selector to indicate the number of events that be retrieved from Splunk to build the graph. The d3.js library and the javascript engine of the browser will become slower as you request more data. Currently, the maximum is set to a safe top of 10000 events but I am actively thinking of ways to solve this.

The first think you need to do is log in the Splunk server with your user and password and a new button will appear if the logging has been successful.

If clustered data is selected and retrieved, the controls buttons allow to show the density of the different clusters.


## Support

This first release has been supported by the Google Summer of Code 2012 program and mentored by The Honeynet Project.

## Contact

You can reach the main developer at hgascon@mail.de.


