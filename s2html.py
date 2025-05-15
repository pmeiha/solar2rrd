#!/usr/bin/env python3

import argparse

import os
#import time
import datetime  
#import getopt
import sys
#import math
import csv
import rrdtool

#datadir = "/data/solar2rrd"
#mainpath = "s2.html"
#pngdir = f'{datadir}/png'
#htmlfile = f'{pngdir}/s2.html'
#tagpath = ""
# monthfile = False

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
  
  global rrdfile, inputfile, debug, debug1, daemonAddr, pngdir, htmlfile, tagpath, mainpath, monthfile

  parser = argparse.ArgumentParser(description="read the given csv file and store them in the rrd database")
  parser.add_argument("-D", "--debug", help="debug level (1=warning 2=info 3=debug 4=all)", default=0, type=int)
  parser.add_argument("-A", "--debug1", help="debug absolut level (10=warning 20=info 30=debug 4=all)", default=0, type=int)
  # parser.add_argument("-A", "--debug1", help="debug absolut level (10=warning 20=info 30=debug 4=all)", default=2, type=int)
  #parser.add_argument("-r", "--rrdfile", help="rrd db file name (default /data/solar2rrd/rrd/s2.rrd", default="/data/solar2rrd/rrd/s2.rrd")
  parser.add_argument("-r", "--rrdfile", help="rrd db file name (default rrd/s2.rrd", default="rrd/s2.rrd")
  parser.add_argument("-d", "--daemon", help="rrdcached address", default="")
  #parser.add_argument("-p", "--pngdirectory", help="directory for the resulting graph (default $datadir)", default="/data/solar2rrd/png")
  parser.add_argument("-p", "--pngdirectory", help="directory for the resulting graph (default $datadir)", default="png")
  parser.add_argument("-H", "--htmlfile", help="main html filename located in png directory", default="s2.html")
  parser.add_argument("-t", "--tagpath", help="html path for the resulting graph", default="")
  parser.add_argument("-m", "--monthfile", help="genarate also week and month ... graph (default day graphs only)", default=False, action='store_true')
  
  args = parser.parse_args()
  
  rrdfile = args.rrdfile
  debug = args.debug
  debug1 = args.debug1
  daemonAddr = args.daemon
  pngdir = args.pngdirectory 
  htmlfile = args.htmlfile
  tagpath = args.tagpath
  monthfile = args.monthfile
  mainpath = f'{tagpath}{htmlfile}'

  fEchoDebug(1,'RRDFILE     :' + rrdfile)
  fEchoDebug(1,'DEBUG       :' + str(debug))
  fEchoDebug(1,'DEBUG1      :' + str(debug1))
  fEchoDebug(1,'DAEMONADDR  :' + daemonAddr)
  fEchoDebug(1,'pngdirectory:' + pngdir)
  fEchoDebug(1,'htmlfile    :' + htmlfile)
  fEchoDebug(1,'tagpath     :' + tagpath)
  fEchoDebug(1,'monthfile   :' + str(monthfile))

  if not os.access(rrdfile, os.R_OK):
    print (sys.argv[0], ": argument -i ",rrdfile," is missing or ",rrdfile," is not readable")
    sys.exit(1)

  return True

#-----------------------------------------------------------------------------------------------------
# write html haeder
#-----------------------------------------------------------------------------------------------------
def htmlHeader (outdata=[]):

  outdata.extend(
      ['<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">',
       '<HTML>',
       '<HEAD>',
       '<TITLE>PV-Data</TITLE>',
       '</HEAD>',
       '<BODY BGCOLOR="#F0F0F0">'
      ] 
    )
  
  return outdata

#-----------------------------------------------------------------------------------------------------
# write html trailer
#-----------------------------------------------------------------------------------------------------
def htmlEnd (outdata=[]):

  outdata.extend(
      ['</BODY>',
       '</HTML>',
      ] 
    )
  
  return outdata

#-----------------------------------------------------------------------------------------------------
# getime from stamp
#-----------------------------------------------------------------------------------------------------
def getTimeFromStamp(stamp = 1):

  #d = datetime.datetime.fromtimestamp(stamp)
  #return d.strftime('%a %d %b %Y %H:%M:%S')
  return ""

#-----------------------------------------------------------------------------------------------------
# getime actual time
#-----------------------------------------------------------------------------------------------------
def getActualTime():

  return datetime.datetime.now().strftime('%a %d %b %Y %H:%M:%S')

#-----------------------------------------------------------------------------------------------------
# fetch values
#-----------------------------------------------------------------------------------------------------
####################################
#fTotal berechnet die Totalen Zähler 
#
# fTotal start end
# 
# start: start date time in seconds sins 1970-01-01
# end  : rnd date time in seconds sins 1970-01-01
#
def fetchValue(start, end):

  global rrdfile

  rrd_result = rrdtool.fetch(rrdfile, 'AVERAGE', '-s', str(start), '-e', str(end) )

  fEchoDebug(4, rrd_result[0])
  fEchoDebug(3, rrd_result[2])

  lResult = []
  for k in rrd_result[1]:
    lResult.append(0)

  selfP = 0  # PV self consumation
  selfB = 0 # Battery self Consumation

  lnr = 0
  for line in rrd_result[2]:
    for i in range(0,len(lResult)):
      if str(line[i]) != "None":
        lResult[i] += line[i]

    # line[0] = PV, line[1] = Ni, line[6] = Netto    
    if str(line[0]) != "None" and str(line[6]) != "None" and str(line[1]) != "None":
      # if PV >= Netto use Netto else use PV
      if line[0] - line[6] >= 0:
        self1 = line[6]
      else:
        self1 = line[0] 

      selfP += self1

      # selfBatterie = Netto - self1 - Netz
      selfB += (line[6] - self1 - line[1])

    lnr += 1
  
  fEchoDebug(4, '%6.2f %6.2f %6.2f %6.2f %6.2f %6.2f' % (lResult[0], lResult[1], lResult[2], lResult[3], lResult[4], lResult[5]))
  fEchoDebug(4, str(lnr))

  dResult = {}

  for i in range(0,len(lResult)):
    # resolution 1 Min * 60 = 1 Std / 1000 = kWh
    dResult[rrd_result[1][i]] = lResult[i] * 60 / 1000

  dResult["selfP"]  = selfP * 60 / 1000
  dResult["selfB"] = selfB * 60 / 1000

  return dResult

#-----------------------------------------------------------------------------------------------------
# generate infra graph
#-----------------------------------------------------------------------------------------------------
def createInfraPng(start="1", end="1", step="1", pngfile="not_correct_png_parameter"):


  tstart = getTimeFromStamp(start)
  tend   = getTimeFromStamp(end)

  vSelf = valuesTotal['Netto']
  if valuesTotal['PV'] - valuesTotal['Netto'] < 0:
    vSelf = valuesTotal['PV']

  rrdtool.graph(
    pngfile,
    "--start", start,
    "--end", end,
    "--title", f'{tstart} - {tend}',
    "--vertical-label", "Wh",
    "--upper-limit", "18000",
    "--step", step,
    "--height", "500",
    "--width", "1500",
    "--rigid",
    f"DEF:PV-raw={rrdfile}:PV:AVERAGE:step={step}",
    f"DEF:Ni-raw={rrdfile}:Ni:AVERAGE:step={step}",
    f"DEF:Ne-raw={rrdfile}:Ne:AVERAGE:step={step}",
    f"DEF:SoBat-raw={rrdfile}:SoBat:AVERAGE:step={step}",
    f"DEF:NeBat-raw={rrdfile}:NeBat:AVERAGE:step={step}",
    f"DEF:SoNe-raw={rrdfile}:SoNe:AVERAGE:step={step}",
    f"DEF:BatNe-raw={rrdfile}:BatNe:AVERAGE:step={step}",
    f"DEF:Netto-raw={rrdfile}:Netto:AVERAGE:step={step}",
    "CDEF:PV=PV-raw,3600,*",
    "CDEF:Ni=Ni-raw,3600,*",
    "CDEF:Ne=Ne-raw,3600,*",
    "CDEF:Netto=Netto-raw,3600,*",
    "CDEF:SoBat=SoBat-raw,3600,*",
    "CDEF:NeBat=NeBat-raw,3600,*",
    "CDEF:SoNe=SoNe-raw,3600,*",
    "CDEF:BatNe=BatNe-raw,3600,*",
    "CDEF:Self1=PV,Netto,-",
    "CDEF:Self=Self1,0,GE,Netto,PV,IF",
    f"AREA:Netto#003dff:BattVerbrauch {valuesTotal['selfB']:.2f} kWh",
    f"AREA:Self#007215:PvVerbrauch {valuesTotal['selfP']:.2f} kWh",
    f"AREA:SoBat#fdce00:SoBat {valuesTotal['SoBat']:.2f} kWh:STACK",
    f"AREA:SoNe#b1fd00:SoNe {valuesTotal['SoNe']:.2f} kWh:STACK",
    f"AREA:Ni#FF0000:NetzImport {valuesTotal['Ni']:.2f} kWh",
    f"AREA:NeBat#dc4646:NeBat {valuesTotal['NeBat']:.2f} kWh",
    f"AREA:BatNe#00fd5c:BatNe {valuesTotal['BatNe']:.2f} kWh TotalVerbrauch {valuesTotal['Netto']:.2f} kWh",
    f"LINE:PV#002a08:TotalPV {valuesTotal['PV']:.2f} kWh"
  )

#-----------------------------------------------------------------------------------------------------
# generate Device graph
#-----------------------------------------------------------------------------------------------------
def createDevPng(start="", end="", step="1", pngfile="not_correct_png_parameter", dev="", label="", max=""):


  tstart = getTimeFromStamp(start)
  tend   = getTimeFromStamp(end)

  rrdtool.graph(
    pngfile,
    "--start", start,
    "--end", end,
    "--title", f'{tstart} - {tend}',
    "--vertical-label", "Wh",
    "--upper-limit", max,
    "--step", step,
    "--height", "500",
    "--width", "1500",
    "--rigid",
    f"DEF:NN-raw={rrdfile}:NN{dev}:AVERAGE:step={step}",
    f"DEF:NH-raw={rrdfile}:NH{dev}:AVERAGE:step={step}",
    f"DEF:SN-raw={rrdfile}:SN{dev}:AVERAGE:step={step}",
    f"DEF:SH-raw={rrdfile}:SH{dev}:AVERAGE:step={step}",
    f"DEF:BN-raw={rrdfile}:BN{dev}:AVERAGE:step={step}",
    f"DEF:BH-raw={rrdfile}:BH{dev}:AVERAGE:step={step}",
    "CDEF:Netz=NN-raw,NH-raw,+,3600,*,",
    "CDEF:Sonne=SN-raw,SH-raw,+,3600,*,",
    "CDEF:Battery=BN-raw,BH-raw,+,3600,*,",
    f"AREA:Sonne#ffdf36:{label} Sonne {(valuesTotal[f'SN{dev}']+valuesTotal[f'SH{dev}']):.2f} kWh",
    f"AREA:Battery#4fd5a9:{label} Batterie {(valuesTotal[f'BN{dev}']+valuesTotal[f'BH{dev}']):.2f} kWh:STACK",
    f"AREA:Netz#ff015b:{label} Netz {(valuesTotal[f'NN{dev}']+valuesTotal[f'NH{dev}']):.2f} kWh:STACK",
    "LINE:Sonne#776816",
    "LINE:Battery#2a785f::STACK",
    "LINE:Netz#771638::STACK"
  )  

#-----------------------------------------------------------------------------------------------------
# write list to file
#-----------------------------------------------------------------------------------------------------
def writeFile(list = [], filename = ""):

  with open(filename, "w") as outfile:
    outfile.write("\n".join(list))


######################################################################################################
# start main
######################################################################################################

getparameter()

now = datetime.datetime.now()
end = now.strftime("%s")
std = (now - datetime.timedelta(days=1,hours=1)).strftime("%s")
stw = (now - datetime.timedelta(days=7,hours=1)).strftime("%s")
stm = (now - datetime.timedelta(days=32,hours=1)).strftime("%s")
stj = (now - datetime.timedelta(days=366,hours=1)).strftime("%s")

print(getActualTime(),"fetch day values")

valuesTotal = fetchValue(std, end)

print(getActualTime(),"generate infra day")

createInfraPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2infra_day.png")

print(getActualTime(),"generate dev day")

createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2Re_day.png", dev = "Rest", label = "RestVerbraucher"        , max = "11000")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2Wp_day.png", dev = "Wp"  , label = "Wärmepumpe"             , max = "5000")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2La_day.png", dev = "La"  , label = "Ladestation"            , max = "13000")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2IT_day.png", dev = "IT"  , label = "IT"                     , max = "800")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2Lk_day.png", dev = "Lk"  , label = "Luftentfewuchter Keller", max = "500")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2Bg_day.png", dev = "Bg"  , label = "Bewässerung Garten"     , max = "100")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2Bt_day.png", dev = "Bt"  , label = "Bewässerung Topf"       , max = "20")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2Bh_day.png", dev = "Bh"  , label = "Begleitheizung"         , max = "1000")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2Zh_day.png", dev = "Zh"  , label = "Zusatzheizung"          , max = "3000")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2W1_day.png", dev = "W1"  , label = "Weinacht1"              , max = "1000")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2W2_day.png", dev = "W2"  , label = "Weihnacht2"             , max = "1000")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2Wa_day.png", dev = "Wa"  , label = "Waschen"                , max = "2800")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2Tr_day.png", dev = "Tr"  , label = "Trocknen"               , max = "2800")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2Fe_day.png", dev = "Fe"  , label = "Frigo Estrich"          , max = "500")
createDevPng (start = std, end = end, step = "60", pngfile = f"{pngdir}/s2Fk_day.png", dev = "Fk"  , label = "Frigo Keller"           , max = "500")

if monthfile:

  print(getActualTime(),"fetch week values")

  valuesTotal = fetchValue(stw, end)

  print(getActualTime(),"generate infra week")

  createInfraPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2infra_week.png")

  print(getActualTime(),"generate dev week")

  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2Re_week.png", dev = "Rest", label = "RestVerbraucher"        , max = "11000")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2Wp_week.png", dev = "Wp"  , label = "Wärmepumpe"             , max = "5000")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2La_week.png", dev = "La"  , label = "Ladestation"            , max = "13000")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2IT_week.png", dev = "IT"  , label = "IT"                     , max = "800")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2Lk_week.png", dev = "Lk"  , label = "Luftentfewuchter Keller", max = "500")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2Bg_week.png", dev = "Bg"  , label = "Bewässerung Garten"     , max = "100")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2Bt_week.png", dev = "Bt"  , label = "Bewässerung Topf"       , max = "20")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2Bh_week.png", dev = "Bh"  , label = "Begleitheizung"         , max = "1000")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2Zh_week.png", dev = "Zh"  , label = "Zusatzheizung"          , max = "3000")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2W1_week.png", dev = "W1"  , label = "Weinacht1"              , max = "1000")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2W2_week.png", dev = "W2"  , label = "Weihnacht2"             , max = "1000")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2Wa_week.png", dev = "Wa"  , label = "Waschen"                , max = "2800")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2Tr_week.png", dev = "Tr"  , label = "Trocknen"               , max = "2800")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2Fe_week.png", dev = "Fe"  , label = "Frigo Estrich"          , max = "500")
  createDevPng (start = stw, end = end, step = "600", pngfile = f"{pngdir}/s2Fk_week.png", dev = "Fk"  , label = "Frigo Keller"           , max = "500")

  print(getActualTime(),"fetch month values")

  valuesTotal = fetchValue(stm, end)

  print(getActualTime(),"generate infra month")

  createInfraPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2infra_mnt.png")

  print(getActualTime(),"generate dev month")

  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2Re_mnt.png", dev = "Rest", label = "RestVerbraucher"        , max = "11000")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2Wp_mnt.png", dev = "Wp"  , label = "Wärmepumpe"             , max = "5000")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2La_mnt.png", dev = "La"  , label = "Ladestation"            , max = "13000")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2IT_mnt.png", dev = "IT"  , label = "IT"                     , max = "800")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2Lk_mnt.png", dev = "Lk"  , label = "Luftentfewuchter Keller", max = "500")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2Bg_mnt.png", dev = "Bg"  , label = "Bewässerung Garten"     , max = "100")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2Bt_mnt.png", dev = "Bt"  , label = "Bewässerung Topf"       , max = "20")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2Bh_mnt.png", dev = "Bh"  , label = "Begleitheizung"         , max = "1000")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2Zh_mnt.png", dev = "Zh"  , label = "Zusatzheizung"          , max = "3000")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2W1_mnt.png", dev = "W1"  , label = "Weinacht1"              , max = "1000")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2W2_mnt.png", dev = "W2"  , label = "Weihnacht2"             , max = "1000")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2Wa_mnt.png", dev = "Wa"  , label = "Waschen"                , max = "2800")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2Tr_mnt.png", dev = "Tr"  , label = "Trocknen"               , max = "2800")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2Fe_mnt.png", dev = "Fe"  , label = "Frigo Estrich"          , max = "500")
  createDevPng (start = stm, end = end, step = "600", pngfile = f"{pngdir}/s2Fk_mnt.png", dev = "Fk"  , label = "Frigo Keller"           , max = "500")

  print(getActualTime(),"fetch year values")

  valuesTotal = fetchValue(stj, end)

  print(getActualTime(),"generate infra year")

  createInfraPng (start = stj, end = end, step = "3600", pngfile = f"{pngdir}/s2infra_year.png")

print(getActualTime(),"write htmlfiles")

htmlmain = htmlHeader([])

htmlmain.append(f"<a href='{tagpath}s2Re.html'>RestVerbraucher        {tagpath}s2Re.html</a>")
htmlmain.append(f"<a href='{tagpath}s2Wp.html'>Wärmepumpe             {tagpath}s2Wp.html</a>")
htmlmain.append(f"<a href='{tagpath}s2La.html'>Ladestation            {tagpath}s2La.html</a>")
htmlmain.append(f"<a href='{tagpath}s2IT.html'>IT                     {tagpath}s2IT.html</a>")
htmlmain.append(f"<a href='{tagpath}s2Lk.html'>Luftentfewuchter Keller{tagpath}s2Lk.html</a>")
htmlmain.append(f"<a href='{tagpath}s2Bg.html'>Bewässerung Garten     {tagpath}s2Bg.html</a>")
htmlmain.append(f"<a href='{tagpath}s2Bt.html'>Bewässerung Topf       {tagpath}s2Bt.html</a>")
htmlmain.append(f"<a href='{tagpath}s2Bh.html'>Begleitheizung         {tagpath}s2Bh.html</a>")
htmlmain.append(f"<a href='{tagpath}s2Zh.html'>Zusatzheizung          {tagpath}s2Zh.html</a>")
htmlmain.append(f"<a href='{tagpath}s2W1.html'>Weinacht1              {tagpath}s2W1.html</a>")
htmlmain.append(f"<a href='{tagpath}s2W2.html'>Weihnacht2             {tagpath}s2W2.html</a>")
htmlmain.append(f"<a href='{tagpath}s2Wa.html'>Waschen                {tagpath}s2Wa.html</a>")
htmlmain.append(f"<a href='{tagpath}s2Tr.html'>Trocknen               {tagpath}s2Tr.html</a>")
htmlmain.append(f"<a href='{tagpath}s2Fe.html'>Frigo Estrich          {tagpath}s2Fe.html</a>")
htmlmain.append(f"<a href='{tagpath}s2Fk.html'>Frigo Keller           {tagpath}s2Fk.html</a>")

htmlmain.append("<p>Tages Graphen</p>")

htmlmain.append(f"<IMG SRC='{tagpath}s2infra_day.png' ALT='Vrbrauchsgraph'><br>")
htmlmain.append(f"<IMG SRC='{tagpath}s2infra_week.png' ALT='Verbrauchsgraph'><br>")
htmlmain.append(f"<IMG SRC='{tagpath}s2infra_mnt.png' ALT='Verbrauchsgraph'><br>")
htmlmain.append(f"<IMG SRC='{tagpath}s2infra_year.png' ALT='Verbrauchsgraph'><br>")

htmlmain.append(f"<a href='{tagpath}s2Re.html'>RestVerbraucher        {tagpath}s2Re.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2Wp.html'>Wärmepumpe             {tagpath}s2Wp.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2La.html'>Ladestation            {tagpath}s2La.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2IT.html'>IT                     {tagpath}s2IT.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2Lk.html'>Luftentfewuchter Keller{tagpath}s2Lk.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2Bg.html'>Bewässerung Garten     {tagpath}s2Bg.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2Bt.html'>Bewässerung Topf       {tagpath}s2Bt.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2Bh.html'>Begleitheizung         {tagpath}s2Bh.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2Zh.html'>Zusatzheizung          {tagpath}s2Zh.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2W1.html'>Weinacht1              {tagpath}s2W1.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2W2.html'>Weihnacht2             {tagpath}s2W2.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2Wa.html'>Waschen                {tagpath}s2Wa.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2Tr.html'>Trocknen               {tagpath}s2Tr.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2Fe.html'>Frigo Estrich          {tagpath}s2Fe.html</a><br>")
htmlmain.append(f"<a href='{tagpath}s2Fk.html'>Frigo Keller           {tagpath}s2Fk.html</a><br>")

htmlmain = htmlEnd(htmlmain)

writeFile(htmlmain, f"{pngdir}/{htmlfile}") 

for dev in ["s2Re","s2Wp","s2La","s2IT","s2Lk","s2Bg","s2Bt","s2Bh","s2Zh","s2W1","s2W2","s2Wa","s2Tr","s2Fe","s2Fk"]:

  htmlmain = htmlHeader([])

  htmlmain.append(f"<a href='{tagpath}s2Re.html'>RestVerbraucher        {tagpath}s2Re.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2Wp.html'>Wärmepumpe             {tagpath}s2Wp.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2La.html'>Ladestation            {tagpath}s2La.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2IT.html'>IT                     {tagpath}s2IT.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2Lk.html'>Luftentfewuchter Keller{tagpath}s2Lk.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2Bg.html'>Bewässerung Garten     {tagpath}s2Bg.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2Bt.html'>Bewässerung Topf       {tagpath}s2Bt.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2Bh.html'>Begleitheizung         {tagpath}s2Bh.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2Zh.html'>Zusatzheizung          {tagpath}s2Zh.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2W1.html'>Weinacht1              {tagpath}s2W1.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2W2.html'>Weihnacht2             {tagpath}s2W2.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2Wa.html'>Waschen                {tagpath}s2Wa.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2Tr.html'>Trocknen               {tagpath}s2Tr.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2Fe.html'>Frigo Estrich          {tagpath}s2Fe.html</a>")
  htmlmain.append(f"<a href='{tagpath}s2Fk.html'>Frigo Keller           {tagpath}s2Fk.html</a>")

  htmlmain.append(f"<a href='{mainpath}'>Infra</a><br>")
  htmlmain.append(f"<IMG SRC='{tagpath}{dev}_day.png' ALT='Verbrauchsgraph'><br>")
  htmlmain.append(f"<a href='{mainpath}'>Infra</a><br>")
  htmlmain.append(f"<IMG SRC='{tagpath}{dev}_week.png' ALT='Verbrauchsgraph'><br>")
  htmlmain.append(f"<a href='{mainpath}'>Infra</a><br>")
  htmlmain.append(f"<IMG SRC='{tagpath}{dev}_mnt.png' ALT='Verbrauchsgraph'><br>")
  htmlmain.append(f"<a href='{mainpath}'>Infra</a><br>")
    
  htmlmain = htmlEnd(htmlmain)

  writeFile(htmlmain, f"{pngdir}/{dev}.html") 
           
print(getActualTime(),"end")

