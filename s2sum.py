import os
import sys
# import requests
import logging
# import json
# import rrdtool
# import time
# from datetime import datetime, timezone, timedelta, tzinfo
# from zoneinfo import ZoneInfo
# import calendar
import csv
# from pwrdata import PowerDataList, PowerDataDict
# import urllib.parse
import argparse
import pprint

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s:%(funcName)s:%(lineno)d:%(message)s',encoding='utf-8', level=logging.WARNING)

glob = {
}

######################################################################################################
# start main
######################################################################################################


parser = argparse.ArgumentParser(description='summarize solar data')
parser.add_argument('-d','--directory',help='directory to search for file',default="data-in")
#parser.add_argument('-s','--filestart',help='start for the filenames ',default="")
parser.add_argument('-s','--filestart',help='start for the filenames ',default="2025-02")
#parser.add_argument('-e','--fileend',help='end of the filename',default=".csv")
parser.add_argument('-e','--fileend',help='end of the filename',default="min.csv")
#parser.add_argument('-o','--outfile',help='output file for the summary',required=True)
parser.add_argument('-o','--outfile',help='output file for the summary',default="data-out/2025-02-sum.csv")

parser.add_argument('-a','--add',help='add the last line from all the files', action='store_true', default=False)

parser.add_argument('-l','--loglevel',help='loglevel default warning or higher', action='count', default=0)

args = parser.parse_args()

match args.loglevel:
    case 2:
        logger.setLevel(logging.DEBUG)
    case 1:
        logger.setLevel(logging.INFO)

glob['inDir'] = args.directory
glob['filestart'] = args.filestart
glob['fileend'] = args.fileend
glob['outfile'] = args.outfile

glob['add'] = args.add



# pp = pprint.PrettyPrinter(indent=4)
# pp.pprint(timetable)


filestart = [ filestart for filestart in sorted(os.listdir(path=glob['inDir'])) if filestart.startswith(glob['filestart']) ]
filename = [ filename for filename in filestart if filename.endswith(glob['fileend']) ]
fileout = glob['outfile']

outcontent = []

first = True

for fn in filename:
    filein = os.path.join(glob['inDir'],fn)

    print(filein)
     
    filecontent = []
    with open(filein) as inf:
        reader = csv.reader(inf, delimiter=';')
        for row in reader:
            filecontent.append(row)
    
    if first:
        outcontent.append(filecontent[0])
        if glob['add']:
            outsumm = ["Summary",""]
            for s in range(2,len(filecontent[-1])):
                outsumm.append(float(filecontent[-1][s]))
        first = False
    else:
        if glob['add']:
            for s in range(2,len(filecontent[-1])):
                outsumm[s] += float(filecontent[-1][s])

    outcontent.append(filecontent[-1])

    # print("cont", filecontent[-1])
    # print("summ", outsumm)

if glob['add']:
    outsumm[0] = f'{glob['filestart']} {glob['fileend']} Summary'
    outsumm[1] = ""
    outsumm[19] = ""
    outsumm[20] = ""
    outsumm[21] = ""
    outcontent.append(outsumm)

print(fileout)
with open(fileout, 'w') as outf:
    writer = csv.writer(outf, delimiter=';')
    writer.writerows(outcontent)

