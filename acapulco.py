
__author__ = 'hgascon'

import sys
import optparse

class Dataset():
    """
    """

    def __init__(self, log_file):
        self.parser(log_file)
        self.dataset = {}

    def parser(self, log_file):
        """
        Read every line in the log file and call the
        corresponding parsing function for each data channel.
        """

        fd = open(log_file, 'r')
        line = fd.readline()
        while (line != "" ):
            line.replace( "\n", "" )
            line = line.split(" ")
            channel = line[3]
            data = " ".join(line[6:])
            if channel is "cuckoo.analysis":
                self.cuckooAnalysis(data)
            elif channel is "dionaea.capture":
                self.dionaeaCapture(data)
            elif channel is "dionaea.dcerpcrequests":
                self.dionaeaDcerpcRequests(data)
            elif channel is "dionaea.shellcodeprofiles":
                self.dionaeaShellCodeProfiles(data)
            elif channel is "mwbinary.dionaea.sensorunique":
                self.mwbinaryDionaeaSensorUnique(data)
            elif channel is "tip":
                self.tip(data)
            line = fd.readline()

    def cuckooAnalysis(self, data):
        """
        """
        return

    def dionaeaCapture(self, data):
        """
        """
        # {"url": "http://186.210.175.254:3700/ghwrpjc", "daddr": "161.53.74.106",
        # "saddr": "186.210.175.254", "dport": "445", "sport": "2264",
        # "sha512": "15073759dc05ce5bc0095b20de19f05560869770bc97be0f6809036cae3db4ed9244985812d4c99f5a53dfd9cbaee46220f83e2823e629c6f8f545187c8fc627",
        # "md5": "fead84c5df2e585749a8da2ce583c926"}
        a = eval(data)
        return

    def dionaeaDcerpcRequests(self, data):
        """
        """
        # {"uuid": "4b324fc8-1670-01d3-1278-5a47bf6ee188", "daddr": "140.110.108.201",
        # "opnum": 31, "saddr": "114.24.51.222", "dport": "445", "sport": "2613"}
        a = eval(data)
        return

    def dionaeaShellCodeProfiles(self, data):
        """
        """
        # {"profile": "[\n    {\n        \"call\": \"LoadLibraryA\",\n
        #       \"args\" : [ \n                \"urlmon\"\n        ],\n
        #        \"return\" : \"0x7df20000\"\n    },\n
        #   {\n        \"call\": \"URLDownloadToFile\",\n        \"args\" : [ \n
        #                \"\",\n                \"http:\\/\\/114.24.51.222:9238\\/rnku\",\n
        #               \"x.\",\n            \"0\",\n            \"0\"\n        ],\n
        #        \"return\":  \"0\"\n    },\n    {\n        \"call\": \"LoadLibraryA\",\n
        #        \"args\" : [ \n                \"x.\"\n        ],\n
        #       \"return\" : \"0x00000000\"\n    },\n    {\n        \"call\": \"ExitThread\",\n
        #        \"args\" : [ \n            \"0\"\n        ],\n        \"return\":  \"0\"\n    }\n]"}
        a = eval(data)
        return

    def glastopfEventsAnon(self, data):
        """
        """
        # ["2012-05-20 09:31:34", "66.249.68.174", "/admin/8003/cgi-bin/ospfd.conf",
        # "unknown", "db299ce504f8697376da10c866ffb49fc8bf5263be0fedd31cd79f85"]
        a = eval(data)
        return

    def mwbinaryDionaeaSensorUnique(self, data):
        """
        """
        return

    def tip(self, data):
        """
        """
        return

def main(data):
    """
    """
    dataset = Dataset(data)
    return 0

def opts():
    usage = "usage: %prog [<data>]"
    parser = optparse.OptionParser(usage)
    options, args = parser.parse_args()
    data = args[0]
    if len(args) < 1:
        parser.error('You need to give the file name <data> where hpfeeds data is logged.')

    return options, data

if __name__ == '__main__':
    options, data  = opts()
    try:
        sys.exit(main(data))
    except KeyboardInterrupt:
        sys.exit(0)