#!/usr/bin/env python

import os
import sys
import requests
import logging
# import json
import rrdtool
# import time
from datetime import datetime, timezone, timedelta, tzinfo
from zoneinfo import ZoneInfo
# import calendar
# import csv
# from pwrdata import PowerDataList, PowerDataDict
# import urllib.parse
import argparse
# import pprint

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s:%(funcName)s:%(lineno)d:%(message)s',encoding='utf-8', level=logging.WARNING)

#-----------------------------------------------------------------------------------------------------
# get command line parameter
#-----------------------------------------------------------------------------------------------------
def getparameter():
  
  global boxUrl, boxDev, rrdfile, daemonAddr

  parser = argparse.ArgumentParser(description="get soc data from the battery")
  parser.add_argument("-u", "--url", help="url to solarmanager box (default http://10.42.10.11/v2/point)", default="http://10.42.10.11/v2/point")
  parser.add_argument("-D", "--device", help="url to solarmanager box (default http://10.42.10.11/v2/devices)", default="http://10.42.10.11/v2/devices")
  #parser.add_argument("-r", "--rrdfile", help="rrd db file name (default /data/solar2rrd/rrd/s2_batt.rrd", default="/data/solar2rrd/rrd/s2_batt.rrd")
  parser.add_argument("-r", "--rrdfile", help="rrd db file name (default rrd/s2.rrd)", default="rrd/s2_batt.rrd")
  parser.add_argument("-d", "--daemon", help="rrdcached address", default="")
  
  args = parser.parse_args()
  
  boxUrl = args.url
  boxDev = args.device
  rrdfile = args.rrdfile
  daemonAddr = args.daemon

  #fEchoDebug(1,'RRDFILE   :' + rrdfile)
  #fEchoDebug(1,'DAEMONADDR:' + daemonAddr)
    
  return True

#-----------------------------------------------------------------------------------------------------
# create new rrd file
#-----------------------------------------------------------------------------------------------------
def createFile(file='', daemonAddr="" ):

  data_sources=['DS:BatSOC:GAUGE:600:0:100',
                'DS:BatPwr:GAUGE:600:U:U',
                'DS:CarSOC:GAUGE:600:0:100',
                'DS:CarPwr:GAUGE:600:U:U',]

  if daemonAddr == "":
    rrdtool.create(file,
                 '--start', '1738364400',
                 '--step', '60',
                 data_sources,
                 'RRA:AVERAGE:0.8:1:90d',
                 'RRA:AVERAGE:0.8:1h:18M')                 
  else:  
    rrdtool.create(file,
                 '--start', '1738364400',
                 '--step', '60',
                 '--daemon', f'"{daemonAddr}"',
                 data_sources,
                 'RRA:MAX:0.8:1:90d',
                 'RRA:MAX:0.8:1h:18M')                 

#-----------------------------------------------------------------------------------------------------
# read data from csv file
#-----------------------------------------------------------------------------------------------------
def rrdUpdate(rrdfile="", value="", daemonAddr=""):

  if daemonAddr == "":       
    rrdtool.update(rrdfile,
                 '--skip-past-updates',
                 value)
  else:  
    rrdtool.update(rrdfile,
                 '--skip-past-updates',
                 '--daemon', f'"{daemonAddr}"',
                 value)

#-----------------------------------------------------------------------------------------------------
# send with get methode
#-----------------------------------------------------------------------------------------------------
def s2rrd_sendGet(url="", hdr=""):

    try:
        response = requests.get(url, headers=hdr)

    except OSError:
        logger.error('No connection to the server!')
        return None

   # check if the request is successful
    if response.status_code == 200:
        logger.info('Status 200, OK')
        return response.json()

    else:
        logger.error(f'JSON data request not successful!. {url}\n{response.status_code}')
        return None

#-----------------------------------------------------------------------------------------------------
# calculate min in UTC from start in local plus hour
#-----------------------------------------------------------------------------------------------------
def getLocal_min(ISO_UTC=""):

    #return datetime.fromisoformat(ISO_UTC).astimezone(ZoneInfo("Europe/Zurich")).strftime('%H:%M %d-%m-%Y')
    return datetime.fromisoformat(ISO_UTC).astimezone(ZoneInfo("Europe/Zurich")).strftime('%s')

######################################################################################################
# start main
######################################################################################################

getparameter()

devData =  s2rrd_sendGet(url=boxDev)
userData = s2rrd_sendGet(url=boxUrl)
deviceData = {}

if not os.access(rrdfile, os.R_OK):
  print (sys.argv[0], ": rrdfile", rrdfile, "not exists, create it")
  createFile(rrdfile, daemonAddr=daemonAddr)

# print(devData)
# print(userData['devices'])

for dev in devData:
   # print('description',dev['description'])
   # print('deviceId',dev['deviceId'])
   # print('name',dev['name'])
   # print('type',dev['type'])
   deviceData[dev['deviceId']] = dev
   for d in userData['devices']:
     if d['_id'] == dev['deviceId']:
        # print(d)
        for k in d.keys():
           if k != '_id':
            # print(k, d[k])
            deviceData[dev['deviceId']][k] = d[k]
   # print()   

# print(deviceData)      

'''
for d in userData['devices']:
  if d['_id'] == '67891d8fab6230c37b47e7c6':
     print('power   ',d['power'])
     print('soc     ',d['soc'])
'''

val = f"{getLocal_min(userData['t'])}:{deviceData['67891d8fab6230c37b47e7c6']['soc']}:{deviceData['67891d8fab6230c37b47e7c6']['power']}:{deviceData['67986f0ce17a98489d933ff3']['soc']}:{deviceData['67890c7c2939855e34eb97e2']['power']}"

print('Batsoc',deviceData['67891d8fab6230c37b47e7c6']['soc'],
      'BatPower',deviceData['67891d8fab6230c37b47e7c6']['power'],
      'Carsoc',deviceData['67986f0ce17a98489d933ff3']['soc'],
      'CarPower',deviceData['67890c7c2939855e34eb97e2']['power'],
      't',userData['t'], getLocal_min(userData['t']),
      'v',userData['v'],
      'val',val)


# print('socGlob ',userData['soc'])
# timekeyFull = datetime( iYear, iMonth, day, hour=hour, minute=min,  second=0,  tzinfo=ZoneInfo("Europe/Zurich")).strftime('%Y-%m-%dT%H:%M:%S%:z')
# print('t       ',userData['t'], getLocal_min(userData['t']) )    
# print('v       ',userData['v'])    

# print(val)

rrdUpdate(rrdfile=rrdfile, value=val, daemonAddr=daemonAddr)
