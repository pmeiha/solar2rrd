#!/usr/bin/env python3

import argparse

import os
#import time
#import datetime
#import getopt
import sys
#import math
import csv
import rrdtool

###########################################
inputfile=""

###########################################

#-----------------------------------------------------------------------------------------------------
# create new rrd file
#-----------------------------------------------------------------------------------------------------
def createFile(file=''):
  data_sources=['DS:PV:DDERIVE:600:0:U',
                'DS:Ni:DDERIVE:600:0:U',
                'DS:Ne:DDERIVE:600:0:U',
                'DS:bd:DDERIVE:600:0:U',
                'DS:bc:DDERIVE:600:0:U',
                'DS:Total:DDERIVE:600:0:U',
                'DS:Netto:DDERIVE:600:0:U',
                'DS:SoBat:DDERIVE:600:0:U',
                'DS:NeBat:DDERIVE:600:0:U',
                'DS:SoNe:DDERIVE:600:0:U',
                'DS:BatNe:DDERIVE:600:0:U']

  for dev in ["Rest", "Wp","La","IT","Lk","Bg","Bt","Bh","Zh","W1","W2","Wa","Tr","Fe","Fk"]:
    dsTemp = [f'DS:{dev}:DDERIVE:600:0:U',
              f'DS:NN{dev}:DDERIVE:600:0:U',
              f'DS:NH{dev}:DDERIVE:600:0:U',
              f'DS:SN{dev}:DDERIVE:600:0:U',
              f'DS:SH{dev}:DDERIVE:600:0:U',
              f'DS:BN{dev}:DDERIVE:600:0:U',
              f'DS:BH{dev}:DDERIVE:600:0:U']
    data_sources.extend(dsTemp)
    
  rrdtool.create(file,
                 '--start', '1738364400',
                 '--step', '60',
                 data_sources,
                 'RRA:MAX:0.8:1:90d',
                 'RRA:MAX:0.8:1h:18M',
                 'RRA:MAX:0.8:1d:10y')                 
                                  
#-----------------------------------------------------------------------------------------------------
# write debug messages ??? to change with log
#-----------------------------------------------------------------------------------------------------
def fEchoDebug(level=0,text=''):
  if debug1 == level:
    print (text, file=sys.stderr)
     
  if debug >= level:
    print (text, file=sys.stderr)
         

#-----------------------------------------------------------------------------------------------------
# get command line parameter
#-----------------------------------------------------------------------------------------------------
def getparameter():
  
  global rrdfile, inputfile, debug, debug1

  parser = argparse.ArgumentParser(description="read the given csv file and store them in the rrd database")
  parser.add_argument("-D", "--debug", help="debug level (1=warning 2=info 3=debug 4=all)", default=0, type=int)
  parser.add_argument("-A", "--debug1", help="debug absolut level (10=warning 20=info 30=debug 4=all)", default=0, type=int)
  # parser.add_argument("-A", "--debug1", help="debug absolut level (10=warning 20=info 30=debug 4=all)", default=2, type=int)
  #parser.add_argument("-r", "--rrdfile", help="rrd db file name (default /data/solar2rrd/s2.rrd", default="/data/solar2rrd/s2.rrd")
  parser.add_argument("-r", "--rrdfile", help="rrd db file name (default rrd/s2.rrd", default="rrd/s2.rrd")
  #parser.add_argument("-i", "--inputfile", help="csv input file", required=True)
  parser.add_argument("-i", "--inputfile", help="csv input file", default="data-in/2025-03-28_min.csv")
  args = parser.parse_args()

  rrdfile = args.rrdfile
  inputfile = args.inputfile
  debug = args.debug
  debug1 = args.debug1
  fEchoDebug(1,'RRDFILE   :' + rrdfile)
  fEchoDebug(1,'INPUTFILE :' + inputfile)
  fEchoDebug(1,'DEBUG     :' + str(debug))
  fEchoDebug(1,'DEBUG1    :' + str(debug1))
    
  if not os.access(inputfile, os.R_OK):
    print (sys.argv[0], ": argument -i ",inputfile," is missing or ",inputfile," is not readable")
    sys.exit(1)

  return True

#-----------------------------------------------------------------------------------------------------
# get value from row
#-----------------------------------------------------------------------------------------------------
def getValue(row={}):
   
  keys = ["seconds","PV","Ni","Ne","bdWh","bcWh","Total_Bezug","Netto_Bezug","SoBat","NeBat","SoNe","BatNe"]
  res = "" 

  for i in keys:
    res += f'{row[i]}:'

  keys = ["Rest", "Wp","La","IT","Lk","Bg","Bt","Bh","Zh","W1","W2","Wa","Tr","Fe","Fk"] 

  for i in keys:
    res += f'{row[i]}:{row[f'NN{i}']}:{row[f'NH{i}']}:{row[f'SN{i}']}:{row[f'SH{i}']}:{row[f'BN{i}']}:{row[f'BH{i}']}:'

  # return all except last character ":"
  return res[:-1]

#-----------------------------------------------------------------------------------------------------
# read data from csv file
#-----------------------------------------------------------------------------------------------------
def readdata():

  global rrdfile, inputfile, debug, debug1
    
  with open(inputfile, 'rt', encoding='utf-8-sig') as inf:
    reader = csv.DictReader(inf, delimiter=';')
    for row in reader:
      fEchoDebug(2,str(row))
             
      rrdtool.update(rrdfile,
                     '--skip-past-updates',
                     getValue(row))
      fEchoDebug(2,getValue(row))          

######################################################################################################
# start main
######################################################################################################

getparameter()

if not os.access(rrdfile, os.R_OK):
  print (sys.argv[0], ": rrdfile", rrdfile, "not exists, create it")
  createFile(rrdfile)

readdata()


