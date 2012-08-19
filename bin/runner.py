#!/usr/bin/python
"""
The Honeynet Prokect
Acapulco (Attack Community grAPh COnstruction)
Runner
Hugo Gascon (hgascon@gmail.com)

This module is in charge of creating meta-events from the different
log files saved from hpfeeds channels in the log directory. These meta-events
are saved in a new log file that is indexed by Splunk and will be able to
be requested later by a remote client. Once meta-events are created, a
clustering algorithm (DBSCAN or k-means) runs over the different features and
their values are replaced by the label of the assigned cluster.

Dependencies: numpy, scipy and scikit-learn


"""

__author__ = 'hgascon'

import os
import sys
import json
import re
import hashlib
import optparse
import pickle
import numpy as np
from scipy.spatial import distance
from sklearn import cluster
from iptools import dottedQuadToNum

#keys that are extracted from the selected hpfeeds log files
KEYS = ["time","chan","saddr","sport","dport","daddr","url","hash"]
#selected keys to build clusters from
KEYS_2_CLS = ["saddr","sport","dport","daddr","url"]
#number of clusters k to use with each key from KEY_2_CLS when
#k-means is selected as the clustering algorithms.
NUM_CLUSTERS = [10,10,10,10,10]

def run(log_dir,o_type,o_dir):
    """ Read hpfeeds log files from the log directory configured in
    Splunk and call the adequate function for each type of file in order
    to build one unique type of event (meta-event).

    Args:
        log_dir: the directory where hpfeeds events are stored.
        It is configured in Splunk and should be given as an input
        to this script.
        o_type: the type of output that this will produce in order
        to be read and indexed by Splunk: JSON or CSV.
        o_dir: the output directory where the new file including
        all meta-events and their clustered version will be stored.
        By default, it is the same as the log_dir.

    Returns:
        0 if files are created correctly after clustering of meta-events.

    """

    events = []
    for f in os.listdir(log_dir):
        if f.endswith(".log"):
            if f == "dionaea.capture.log":
                events += dionaea_capture(open(os.path.join(log_dir, f),'r'))
                print "[*] Processing {0}...".format(f)
            elif f == "dionaea.dcerpcrequests.log": 
                events += dionaea_dcerpcrequests(open(os.path.join(log_dir, f),'r'))
                print "[*] Processing {0}...".format(f)
            elif f == "dionaea.capture.anon.log":
                events += dionaea_capture_anon(open(os.path.join(log_dir, f),'r'))
                print "[*] Processing {0}...".format(f)
            elif f == "thug.files.log":
                events += thug_files(open(os.path.join(log_dir, f),'r'))
                print "[*] Processing {0}...".format(f)
            # elif f == "Glastopf.events.in.log":
            #     events += glastopf_events_in(open(os.path.join(log_dir, f),'r'))
            #     print "[*] Processing {0}...".format(f)
            # elif f == "cuckoo.analysis.log":
            #     events += cuckoo_analysis(open(os.path.join(log_dir, f),'r'))
            #     print "[*] Processing {0}...".format(f)
            # elif f == "mwbinary.dionaea.sensorunique.log":
            #     events += mwbinary_dionaea_sensorunique(open(os.path.join(log_dir, f),'r'))
            #     print "[*] Processing {0}...".format(f)
            # elif f == "dionaea.shellcodeprofiles.log":
            #     events += dionaea_shellcodeprofiles(open(os.path.join(log_dir, f),'r'))
            #     print "[*] Processing {0}...".format(f)
            # elif f == "test.feed.log":
            #     events += test_feed(open(os.path.join(log_dir, f),'r'))
            #     print "[*] Processing {0}...".format(f)
            # elif f == "glastopf.events.anon.log":
            #     events += glastopf_events_anon(open(os.path.join(log_dir, f),'r'))
            #     print "[*] Processing {0}...".format(f)
            # elif f == "thug.events.log":
            #     events += thug.events(open(os.path.join(log_dir, f),'r'))
            #     print "[*] Processing {0}...".format(f)
            # elif f == "glastopf.files.log":
            #     events += glastopf_files(open(os.path.join(log_dir, f),'r'))
            #     print "[*] Processing {0}...".format(f)
            # elif f == "dionaea.capture.in.log":
            #     events += dionaea_capture_in(open(os.path.join(log_dir, f),'r'))
            #     print "[*] Processing {0}...".format(f)
            # elif f == "glastopf.sandbox.log":
            #     events += glastopf_sandbox(open(os.path.join(log_dir, f),'r'))
            #     print "[*] Processing {0}...".format(f)
            # elif f == "tip.log":      
            #    events += tip_log(open(os.path.join(log_dir, f),'r'))
            #     print "[*] Processing {0}...".format(f)



    #format data for d3 representation
    events_normal = encode_d3(list(events))

    #save the original list of events
    save(events_normal,o_dir,o_type,"acapulco_normal")

    #compute clusters
    events_cls = cluster_events(list(events))

    #save the clustered list of events
    save(events_cls,o_dir,o_type,"acapulco")

    return 0


def save(events,o_dir,o_type,fname):
    """ Save in disc the new files containing all meta-events
    and their clustered version.

    Args:
        events: a list of meta-events (dictionaries).
        o_type: the type of output that this will produce in order
        to be read and indexed by Splunk: JSON or CSV.
        o_dir: the output directory where the new file including
        all meta-events and their clustered version will be stored.
        By default, it is the same as the log_dir.
        fname: name of the output file
    """

    #Save pickle objects for debbuging.
    #f = open(os.path.join(o_dir, fname+".pickle"),"wb")
    #pickle.dump(events,f)
    #f.close()

    #build output depending on out format
    if o_type == "json":
        out = json_formatter(events)
    elif o_type == "csv":
        out = csv_formatter(events)

    print "[*] Writing output..."
    #open json data file and write event lines
    json_file = open(os.path.join(o_dir, fname+".log"),"wb")
    json_file.write(out)
    json_file.close()


def cluster_events(events_cls,keys=KEYS_2_CLS,n_clusters=NUM_CLUSTERS):
    """ Read the list of meta-events, the keys to be clustered and
    the number of clusters for the k-means algorithm. Calls encoding
    functions for different features in each meta-event and create
    a new list of meta-events where feature values are cluster-label
    encoded.

    Args:
        events_cls: a list of meta-events (dictionaries).
        keys: features to be clustered in each meta-event.
        n_clusters: list of numbers of clusters to use for each features
        when k-means algorithm is used.

    Returns:
        A list of meta-events (dictionaries) where the values of the
        different features are clustered and the new value is the label
        of the assigned cluster.
    """

    #cluster only parameters in KEYS_CLS in all events
    num_cls_d = dict(zip(keys,n_clusters))

    for k in keys:

        #build a dict of original values as keys and
        #encoded vectors as values
        print "[*] Clustering {0}...".format(k)
        value_vector_d, vector_a = encode(events_cls,k)
        
        # 2 algorithms can be used: k-means or DBSCAN
        # vector_label_d = cluster_kmeans(vector_a,num_cls_d[k])
        vector_label_d = cluster_dbscan(vector_a)

        #create a dict of original values and their cluster labels
        for e in events_cls:
            value = e[k]
            vector = value_vector_d[value]
            cluster_label = vector_label_d[str(vector).replace("L","")]
            e[k] = cluster_label

    return events_cls
  
def dionaea_capture(file):
    """ Read a dionaea_capture hpfeeds log file
    and create a list of meta-events according to a previous
    extraction definition.

    Args:
        file: file descriptor of a hpfeed log file.

    Returns:
        A list of meta-events (dictionaries).
    """
    data = file.read()
    dict_list = []
    r = "^(.*) PUBLISH chan=(.*), identifier=(.*), url=(.*), daddr=(.*), saddr=(.*), dport=(.*), sport=(.*), sha512=(.*), md5=(.*)"
    events = []
    #this loop could be possible changed by lambda+map func
    for l in data.split("\n"):
        e = re.findall(r,l)
        if len(e) > 0:
            events += e
    #it is necessary to sort values for each event in each channel
    for e in events:
        values = [e[0],e[1],e[5],e[7],e[6],e[4],e[3],e[9]]
        dict_list.append(dict(zip(KEYS,values)))
    return dict_list

def dionaea_dcerpcrequests(file):
    """ Read a dionaea_dcerpcrequests hpfeeds log file
    and create a list of meta-events according to a previous
    extraction definition.

    Args:
        file: file descriptor of a hpfeed log file.

    Returns:
        A list of meta-events (dictionaries).
    """ 
    data = file.read()
    dict_list = []
    r = "^(.*) PUBLISH chan=(.*), identifier=(.*), uuid=(.*), daddr=(.*), opnum=(.*), saddr=(.*), dport=(.*), sport=(.*)"
    events = []
    for l in data.split("\n"):
        e = re.findall(r,l)
        if len(e) > 0:
            events += e
    for e in events:
        values = [e[0],e[1],e[6],e[8],e[7],e[4],e[3],"0"]
        dict_list.append(dict(zip(KEYS,values)))
    return dict_list

def dionaea_capture_anon(file):
    """ Read a dionaea_capture_anon hpfeeds log file
    and create a list of meta-events according to a previous
    extraction definition.

    Args:
        file: file descriptor of a hpfeed log file.

    Returns:
        A list of meta-events (dictionaries).
    """ 
    data = file.read()
    dict_list = []
    r = "^(.*) PUBLISH chan=(.*), identifier=(.*), script=(.*), type=(.*), id=(.*) server=(.*)"
    events = []
    for l in data.split("\n"):
        e = re.findall(r,l)
        if len(e) > 0:
            events += e
    for e in events:
        values = [e[0],e[1],e[5],"80","0","0.0.0.0",e[3],"0"]
        dict_list.append(dict(zip(KEYS,values)))
    return dict_list

def thug_files(file):
    """ Read a thug_files hpfeeds log file
    and create a list of meta-events according to a previous
    extraction definition.

    Args:
        file: file descriptor of a hpfeed log file.

    Returns:
        A list of meta-events (dictionaries).
    """ 
    data = file.read()
    dict_list = []
    r = "^(.*) PUBLISH chan=(.*), identifier=(.*), url=(.*), type=(.*), sha1=(.*), data=(.*), md5=(.*)"
    events = []
    for l in data.split("\n"):
        e = re.findall(r,l)
        if len(e) > 0:
            events += e
    for e in events:
        values = [e[0],e[1],"0","80","0","0",e[3],e[7]]
        dict_list.append(dict(zip(KEYS,values)))
    return dict_list

# def glastopf_events_in(file):
# def cuckoo_analysis(file):
# def mwbinary_dionaea_sensorunique(file):
# def dionaea_shellcodeprofiles(file):
# def test_feed(file):
# def glastopf_events_anon(file):
# def thug.events(file):
# def glastopf_files(file):
# def dionaea_capture_in(file):
# def glastopf_sandbox(file):
# def tip_log(file):


def cluster_dbscan(vector_a):
    """ Change all original parameter values with cluster labels in
    a list of events using DBSCAN clustering algorithm.

    Args:
        vector_a: array of vectors to cluster.

    Returns:
        A dict where old values are the keys and cluster
        labels are the values.
    """
    # Compute similarities
    D = distance.squareform(distance.pdist(vector_a))
    S = 1 - (D / np.max(D))

    # Compute DBSCAN
    db = cluster.DBSCAN().fit(S)
    core_samples = db.core_sample_indices_
    labels = db.labels_
    
    #create a dict of vectors and their new cluster labels
    vector_l = map(list, vector_a)
    vector_label_d = dict(zip(map(str,vector_l),labels))

    return vector_label_d


def cluster_kmeans(vector_a,n_cls):
    """ Change all original parameter values with cluster labels in
    a list of events.

    Args:
        vector_a: array of vectors to cluster.
        n_cls: number of clusters.

    Returns:
        A dict where old values are the keys and cluster
        labels are the values.
    """
    
    #check if number of points is larger than k
    #if not, use number of points as k
    if len(vector_a) < n_cls:
        n_cls = len(vector_a)

    #calculate n_cls clusters using k-means algorithm
    kmeans = cluster.KMeans(n_cls)
    kmeans.fit(vector_a)
    labels = kmeans.labels_
    
    #create a dict of vectors and their new cluster labels
    vector_l = map(list, vector_a)
    vector_label_d = dict(zip(map(str,vector_l),labels))

    return vector_label_d

def encode_d3(events):
    """ Re-encode all values of a specific parameter 
    to valid numeric d3 representation.

    Args:
        events: list of events.

    Return:
        A list where all events are encoded numeric-like
        way that can be used by d3 to plot them in an axis.
    """

    url_list = [e["url"] for e in events]
    url_enc_d = _str_integer_encode(url_list)

    events_enc = []
    for e in events:
        d = dict(e)
        for p,v in d.items():
            if p == "saddr":
                d[p] = _encode_ip(d[p])
            elif p == "sport":
                d[p] = _encode_port(d[p])
            elif p == "dport":
                d[p] = _encode_port(d[p])
            elif p == "daddr":
                d[p] = _encode_ip(d[p])
            elif p == "url":
                d[p] = url_enc_d[d[p]]
        events_enc.append(d)
    return events_enc


def encode(events_cls,p):
    """ Re-encode all values of a specific parameter 
    to valid representation for clustering.

    Args:
        events_cls: list of event values of parameter.
        p: type of parameter to encode.

    Return:
        A dictionary where all values are encoded in a specific
        way depending on the type of parameter. The keys are the 
        original values and the values are the new encoded values
    """

    value_vector_d = {}
    if p == "saddr":
        for e in events_cls:
            value_vector_d[e[p]] = [_encode_ip(e[p])]
        vector_a = np.array(value_vector_d.values())
        vector_a.shape = (len(vector_a),1)

    elif p == "sport":
        for e in events_cls:
            value_vector_d[e[p]] = [_encode_port(e[p])]
        vector_a = np.array(value_vector_d.values())
        vector_a.shape = (len(vector_a),1)

    elif p == "dport":
        for e in events_cls:
            value_vector_d[e[p]] = [_encode_port(e[p])]
        vector_a = np.array(value_vector_d.values())
        vector_a.shape = (len(vector_a),1)

    elif p == "daddr":
        for e in events_cls:
            value_vector_d[e[p]] = [_encode_ip(e[p])]
        vector_a = np.array(value_vector_d.values())
        vector_a.shape = (len(vector_a),1)

    elif p == "url":
        url_list = [e[p] for e in events_cls]
        value_vector_d = _str_vector_encode(url_list)
        vector_a = np.array(value_vector_d.values())

    return value_vector_d, vector_a


def _encode_ip(ip):
    """ Encode an IP address as an integer

    Args:
        ip: IP address as a string object.

    Returns:
        An IP address encoded as an integer.
    """

    #encode each dotted quad ip string as a integer
    enc_ip = dottedQuadToNum(ip)
    
    #encode each dotted quad ip string as a vector
    #four integers
    # enc_ip = map(int,ip.split("."))
   
    return enc_ip

def _encode_port(port):
    """ Encode a port number as an integer

    Args:
        port: port number as a string object.

    Returns:
        A port number encoded as an integer.
    """

    enc_port = int(port)
    return enc_port


def _encode_url_md5(url_l):
    """ Compute md5 of each URL and encode hash as a number

    Args:
        url_l: a list of urls (strings).

    Returns:
        A list of hashed urls.
    """

    enc_urls = []
    md5 = hashlib.md5()
    for url in url_l:
        md5.update(url)
        digest = md5.hexdigest()
        enc_urls += [int(digest, 16)]
    return enc_urls


def _str_vector_encode(string_list):
    """ Encode a series of strings as vectors and expand
    them with zeros to the max size in the input list.
    Vector encoding is done by using each character integer
    value as a sorted element in the vector.

    Args:
        string_list: a list of strings

    Returns:
        A dict where keys are the original strings
        and values are the encoded vectors.
    """

    s_vector_d = {}
    for s in string_list:
        v = [ord(c) for c in s]
        s_vector_d[s] = v
    m = max([len(v) for v in s_vector_d])
    for s,v in s_vector_d.items():
        s_vector_d[s] = expand(v,m)

    return s_vector_d

def _str_integer_encode(string_list):
    """ Sort all srings alphabetically and encode all 
    of them as integers where its value is the order
    in the sorted list.

    Args:
        string_list: a list of strings

    Returns:
        A dict where keys are the original strings
        and values are the encoded integers as sorted
        alphabetically.
    """

    s_int_d = {}
    string_list.sort()
    s = list(set(string_list))
    for i in range(len(s)):
        s_int_d[s[i]] = i

    return s_int_d

def expand(v,m):
    """ Expand or pad a list with zeros up to a size.

    Args:
        v: list of integers.
        m: size of the resulting vector after padding.

    Returns:
        A expanded vector with zeros of size m
    """

    v += [0]*(m-len(v))
    return v

def json_formatter(events):
    """ Format all new events in one line in json format

    Args:
        events: a list of events (dictionaries).

    Returns:
        The same list formatted as a JSON string object ready
        to write in an output file which is monitored and
        indexed by Splunk.
    """
    o_events = "["
    for d in events:
        s_events = "{"
        for coord in KEYS[2:]:
            s_events += "\"{0}\": {1}, ".format(coord,d[coord])
        s_events = s_events[:-2] + "}, "
        o_events += s_events
    o_events = o_events[:-2] + "]"
    o_events.replace("L","")

    return o_events

def csv_formatter(events):
    """Format all new events one event per line in csv format

    Args:
        events: a list of events (dictionaries).

    Returns:
        The same list formatted as a CSV string object ready
        to write in an output file which is monitored and
        indexed by Splunk.
    """
    out_t = ""
    out = ""
    for d in events:
        out = d["time"] + " "
        for coord in KEYS[1:]:
            out += "{0}={1}, ".format(coord,d[coord])
        out = out[:-2] + "\n"
        out.replace("L","")
        out_t += out
    return out_t


def opts():
    usage = "usage: %prog [options] <log dir>"
    parser = optparse.OptionParser(usage)
    parser.add_option("-o", "--output", dest="output_type",
                      default="csv",
                      help="Output type: csv or json (default %default)")
    parser.add_option("-d", "--outdir", dest="output_dir",
                      default="log dir",
                      help="Output directory (default %default)")
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        parser.error('You need to give the directory name where hpfeeds data is logged.')
        sys.exit(1)
    if options.output_type not in ["json","csv"]:
        parser.print_help()
        parser.error('Output mode can only be "csv" or "json".')        
        sys.exit(1)        
    log_dir = args[0]
    if options.output_dir == "log dir":
        options.output_dir = log_dir
    
    return options, log_dir

if __name__ == '__main__':
    options, log_dir  = opts()
    try:
        sys.exit(run(log_dir,options.output_type,options.output_dir))
    except KeyboardInterrupt:
        sys.exit(0)
