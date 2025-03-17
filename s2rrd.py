import os
import sys
import requests
import logging
# import json
# import rrdtool
import time
from datetime import datetime, timezone, timedelta, tzinfo
from zoneinfo import ZoneInfo
import calendar
import csv
from pwrdata import PowerDataList, PowerDataDict
import urllib.parse
import argparse
import pprint

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s:%(funcName)s:%(lineno)d:%(message)s',encoding='utf-8', level=logging.WARNING)

glob = {
  'S2RRD_UID': os.getenv('S2RRD_UID'),
  'S2RRD_PWD': os.getenv('S2RRD_PWD'),
  'S2RRD_BASE': 'https://cloud.solar-manager.ch',
  'LoginData' : {},
  'LogedIn': False,
  'interval': '10',
  'requesttime': 0,
  'requestinterval': 1,
  'UserData': {
    "status": "",
    "language": "",
    "last_name": "",
    "email": "",
    "first_name": "",
    "country": "",
    "license": "",
    "city": "",
    "note": "",
    "plant": "",
    "street": "",
    "zip": "",
    "kWp": 0,
    "energy_assistant_enable": True,
    "last_login_date": "",
    "user_id": "",
    "registration_date": "",
    "sm_id": "",
    "gateway_id": "",
    "installation_finished": True,
    "hardware_version": "",
    "firmware_version": "",
    "signal": "",
    "last_connection": "",
    "oem": "",
    "installer": "",
    "tariffType": "",
    "device_count": 0,
    "car_count": 0
   },
   'DeviceData': {}
}

#-----------------------------------------------------------------------------------------------------
# login to solar manager cloud
#-----------------------------------------------------------------------------------------------------
def s2rrd_login():

    global glob

    url = f'{glob['S2RRD_BASE']}/v1/oauth/login'
    hdr = {"accept": "application/json", "Content-Type": "application/json" }
    data = {
      "email": glob['S2RRD_UID'],
      "password": glob['S2RRD_PWD']
    }

    return s2rrd_sendLogin(url=url, data=data, hdr=hdr)

#-----------------------------------------------------------------------------------------------------
# login to solar manager cloud
#-----------------------------------------------------------------------------------------------------
def s2rrd_refresh():

    if glob['LogedIn']:
        url = f'{glob['S2RRD_BASE']}/v1/oauth/refresh'
        hdr = {"accept": "application/json", "Content-Type": "application/json", "Authorization" : glob['LoginData']['accessToken']}
        data = {
          "refreshToken": glob['LoginData']['refreshToken']
        }

        return s2rrd_sendLogin(url=url, data=data, hdr=hdr)

    else:
        logger.warning('NOT LogedIn')
        return False    


#-----------------------------------------------------------------------------------------------------
# send with post methode data and stor the result as login data
#-----------------------------------------------------------------------------------------------------
def s2rrd_sendLogin(url="", data="", hdr=""):

    global glob

    loginData = {
        'accessToken': "",
        'refreshToken': "",
        'expiresIn': 0,
        'tokenType': "Bearer",
        'accessClaims': ["Partner"]
    }

    try:
        response = requests.post(url, json=data, headers=hdr)

    except OSError:
        logger.error('No connection to the server!')
        glob['LoginData'] = loginData
        glob['LogedIn'] = False
        return False

   # check if the request is successful
    if response.status_code == 200:
        logger.info('Status 200, OK')
        glob['LoginData'] = response.json()
        glob['LogedIn'] = True
        return True

    else:
        logger.error(f'JSON data request not successful!. {url}\n{response.status_code}')
        glob['LoginData'] = loginData
        glob['LogedIn'] = False
        return False

#-----------------------------------------------------------------------------------------------------
# send with get methode
#-----------------------------------------------------------------------------------------------------
def s2rrd_sendGet(url="", hdr=""):

    global glob

    while glob['requesttime'] > time.time():
        print("wait for request")
        time.sleep(1)

    glob['requesttime'] = time.time() + glob['requestinterval']

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
# get general user informations
#-----------------------------------------------------------------------------------------------------
def s2rrd_users():

    url = f'{glob['S2RRD_BASE']}/v1/users'
    hdr = {"accept": "application/json", "Authorization" : glob['LoginData']['accessToken']}

    userData = s2rrd_sendGet(url=url, hdr=hdr)

    if userData != None:
        glob['UserData'] = userData[0]

    return None

#-----------------------------------------------------------------------------------------------------
# get device list
#-----------------------------------------------------------------------------------------------------
def s2rrd_deviceList():

    url = f'{glob['S2RRD_BASE']}/v1/info/sensors/{glob['UserData']['sm_id']}'
    hdr = {"accept": "application/json", "Authorization" : glob['LoginData']['accessToken']}

    deviceData = s2rrd_sendGet(url=url, hdr=hdr)

    if deviceData != None:
        glob['DeviceData'] = deviceData

    return None

#-----------------------------------------------------------------------------------------------------
# get device id by name
#-----------------------------------------------------------------------------------------------------
def s2rrd_getDeviceId(name = "", type = ""):

    if name != "":
        for device in glob['DeviceData']:
            if 'tag' in device.keys(): 
                if device['tag']['name'] == name:
                    if device['type'] == type or type == "":
                        return device['_id']

    return "NOT_FOUND"

#-----------------------------------------------------------------------------------------------------
# get generic sensor values 
#-----------------------------------------------------------------------------------------------------
def s2rrd_getGenericSensor(id="", start="", end="", interval="10"):

    url = f'{glob['S2RRD_BASE']}/v1/data/sensor/{id}/range?from={start}&to={end}&interval={interval}'
    hdr = {"accept": "application/json", "Authorization" : glob['LoginData']['accessToken']}

    return s2rrd_sendGet(url=url, hdr=hdr)

#-----------------------------------------------------------------------------------------------------
# calculate hour in UTC from start in local plus hour
#-----------------------------------------------------------------------------------------------------
def getUTC_hour(start=0, hour=0):

    s1 = start.split('T')
    startUTC = datetime.fromisoformat(f'{s1[0]}T{hour:02d}:{s1[1].partition(":")[2]}').astimezone(ZoneInfo("UTC")).strftime('%Y-%m-%dT%H:%M:%S%:z')

    return f'{startUTC.split(':')[0]}'

#-----------------------------------------------------------------------------------------------------
# calculate min in UTC from start in local plus hour
#-----------------------------------------------------------------------------------------------------
def getUTC_min(timestamp=0):

    startUTC = datetime.fromisoformat(timestamp).astimezone(ZoneInfo("UTC")).strftime('%Y-%m-%dT%H:%M')

    return startUTC

#-----------------------------------------------------------------------------------------------------
# get consumtion values 
#-----------------------------------------------------------------------------------------------------
def s2rrd_getConsumption(start="", end='', interval="300"):
    
    url = f'{glob['S2RRD_BASE']}/v1/consumption/gateway/{glob['UserData']['sm_id']}/range?from={start}&to={end}&interval={interval}'
    hdr = {"accept": "application/json", "Authorization" : glob['LoginData']['accessToken']}

    return s2rrd_sendGet(url=url, hdr=hdr)

#-----------------------------------------------------------------------------------------------------
# get all entry from powerData from the same timestamp
#-----------------------------------------------------------------------------------------------------
def s2rrd_splitMin(timestamp="", powerData=None):

    result = []
    if powerData != None:
        for i in powerData:
            if 'date' in i.keys():
                if i['date'].startswith(timestamp):
                    result.append(i)

    return result

#-----------------------------------------------------------------------------------------------------
# get all entry from powerData from the same timestamp
#-----------------------------------------------------------------------------------------------------
def s2rrd_splitMinGeneric(timestamp="", powerData=None):

    raw = s2rrd_splitMin(timestamp=timestamp, powerData=powerData)

    summ = 0
    for p in raw:
        summ += p['currentPower'] / 3600 * int(glob['interval'])

    return {'summ':summ, 'raw':raw }

#-----------------------------------------------------------------------------------------------------
# get all entry from powerData from the same timestamp
#-----------------------------------------------------------------------------------------------------
def s2rrd_splitMinGrid(timestamp="", powerData=None):

    raw = s2rrd_splitMin(timestamp=timestamp, powerData=powerData)

    iWh = 0
    eWh = 0

    for p in raw:
        iWh += p['iWh'] # / 3600 * int(glob['interval'])
        eWh += p['eWh'] # / 3600 * int(glob['interval'])

    return {'summ':{'iWh': iWh, 'eWh': eWh }, 'raw':raw }

#-----------------------------------------------------------------------------------------------------
# get all entry from powerData from the same timestamp
#-----------------------------------------------------------------------------------------------------
def s2rrd_splitMinBattery(timestamp="", powerData=None):

    raw = s2rrd_splitMin(timestamp=timestamp, powerData=powerData)

    bdWh = 0
    bcWh = 0
    bdW  = 0
    bcW  = 0

    for p in raw:
        bdWh += p['bdWh']
        bcWh += p['bcWh']
        bdW  += p['bdW']
        bcW  += p['bcW']

    return {'summ':{ "bdWh": bdWh, "bcWh": bcWh, "bdW":bdW, "bcW":bcW }, 'raw':raw }


#-----------------------------------------------------------------------------------------------------
# calculate split sun, battery
# =IF((Wechselrichter-Bat.charge)<0;Wechselrichter;Bat.charge)
#-----------------------------------------------------------------------------------------------------
def getSplit(sun, bat):

    if sun - bat < 0:
        res = sun
    else:
        res = bat    

    return res

#-----------------------------------------------------------------------------------------------------
# calculate hochtarif, niedertarif
#-----------------------------------------------------------------------------------------------------
def getHT(isotime):
    try:
        t = datetime.strptime(isotime, "%Y-%m-%dT%H:%M")
        wDay = t.weekday()
        lYear = t.year
        lHour = t.hour
    except:
        wDay = 7
        lYear = 2024
        lHour = 0

    if ((int(wDay) < 5) and (int(lHour) >= 7) and (int(lHour) < 20)) or ((int(wDay) == 5) and (int(lHour) >= 7) and (int(lHour) < 13) and (int(lYear) < 2023)):
        res = 'H'
    else:
        res = 'N'    

    return res

#-----------------------------------------------------------------------------------------------------
# print the actual device list
#-----------------------------------------------------------------------------------------------------
def s2rrd_printDeviceList():

    for device in glob['DeviceData']:

        print(device['_id'])
        print(device['type'])
        print(device['device_group'])
        print(device['tag']['name'])
        print("")

######################################################################################################
# start main
######################################################################################################


parser = argparse.ArgumentParser(description='get solar data')
parser.add_argument('-d','--day',help='day ',default=31, type=int)
parser.add_argument('-m','--month',help='month ',default=1, type=int)
parser.add_argument('-y','--year',help='year ',default=2025, type=int)

parser.add_argument('-r','--requestinterval',help='time between cloud requests',default='-1', type=int)

parser.add_argument('-l','--loglevel',help='loglevel default warning or higher', action='count', default=0)

args = parser.parse_args()

# get month and year argument
iDay   = args.day
iMonth = args.month
iYear  = args.year

match args.loglevel:
    case 2:
        logger.setLevel(logging.DEBUG)
    case 1:
        logger.setLevel(logging.INFO)

glob['requestinterval'] = int(args.requestinterval)

# login to the cloud
logger.info(f's2rrd_login :{s2rrd_login()}')

# get user information
s2rrd_users()
# logger.info(f'{glob['UserData']}')

# get device information
s2rrd_deviceList()

logger.info(f'{glob['DeviceData']}')

# interval = glob['interval']

mintable = [
    ['Date', 'seconds',
     'PV', 'NNPV', 'NHPV',
     'Ni', 'NNNi', 'NHNi', 'Ne', 'NNNe', 'NHNe',
     'bdWh', 'NNbdWh', 'NHbdWh', 
     'bcWh', 'NNbcWh', 'NHbcWh',
     'Total_Bezug', 'Netto_Bezug','Sonne%', 'Netz%', 'Batterie%',
     'SoBat','NNSoBat', 'NHSoBat', 'NeBat', 'NNNeBat', 'NHNeBat', 'SoNe', 'NNSoNe', 'NHSoNe', 'BatNe', 'NNBatNe', 'NHBatNe',
     'Rest', 'NNRest', 'NHRest', 'SNRest', 'SHRest', 'BNRest', 'BHRest',
     'Wp','NNWp', 'NHWp', 'SNWp', 'SHWp', 'BNWp', 'BHWp',
     'La', 'NNLa', 'NHLa', 'SNLa', 'SHLa', 'BNLa', 'BHLa',
     'IT', 'NNIT', 'NHIT', 'SNIT', 'SHIT', 'BNIT', 'BHIT',
     'Lk', 'NNLk', 'NHLk', 'SNLk', 'SHLk', 'BNLk', 'BHLk',
     'Bg', 'NNBg', 'NHBg', 'SNBg', 'SHBg', 'BNBg', 'BHBg',
     'Bt', 'NNBt', 'NHBt', 'SNBt', 'SHBt', 'BNBt', 'BHBt',
     'Bh', 'NNBh', 'NHBh', 'SNBh', 'SHBh', 'BNBh', 'BHBh',
     'Zh', 'NNZh', 'NHZh', 'SNZh', 'SHZh', 'BNZh', 'BHZh',
     'W1', 'NNW1', 'NHW1', 'SNW1', 'SHW1', 'BNW1', 'BHW1',
     'W2', 'NNW2', 'NHW2', 'SNW2', 'SHW2', 'BNW2', 'BHW2',
     'Wa', 'NNWa', 'NHWa', 'SNWa', 'SHWa', 'BNWa', 'BHWa',
     'Tr', 'NNTr', 'NHTr', 'SNTr', 'SHTr', 'BNTr', 'BHTr',
     'Fe', 'NNFe', 'NHFe', 'SNFe', 'SHFe', 'BNFe', 'BHFe',
     'Fk', 'NNFk', 'NHFk', 'SNFk', 'SHFk', 'BNFk', 'BHFk'
    ]
]

mintableSum = {'Date': ""}

for k in mintable[0][1:]:
    mintableSum[k] = 0

timetable = {}

# for day in range(1,calendar.monthrange(iYear, iMonth)[1]+1 ):
for day in [ iDay ]:  
    #PowerDataDict = {}
    start = datetime( iYear, iMonth, day, hour=0, minute=0,  second=0,  tzinfo=ZoneInfo("Europe/Zurich")).strftime('%Y-%m-%dT%H:%M:%S%:z')
    end   = datetime( iYear, iMonth, day, hour=23, minute=59, second=59, tzinfo=ZoneInfo("Europe/Zurich")).strftime('%Y-%m-%dT%H:%M:%S%:z')
    startH = urllib.parse.quote(start)
    endH   = urllib.parse.quote(end)

    # print(start,end, startH, endH)
    PowerDataDict["Consumption"] = s2rrd_getConsumption( start=startH, end=endH )
    for device in ["Wechselrichter","Verbrauch","Batterie","Wärmepumpe","Ladestation","SmartPlug IT","Luftentfeuchter Keller","Bewässerung Garten",
                   "Bewässerung Topf","Begleitheizung","Zusatzheizung","Weihnacht1","Weihnacht2","Waschen","Trocknen","FrigoE","FrigoK"]:
        PowerDataDict[device] = s2rrd_getGenericSensor(id=s2rrd_getDeviceId(name = device), start=startH, end=endH)

    for hour in range(0, 24):

        for min in range(0, 60):
            timekey = f'{iYear}-{iMonth:02d}-{iDay:02d}T{hour:02d}:{min:02d}'
            timekeyFull = datetime( iYear, iMonth, day, hour=hour, minute=min,  second=0,  tzinfo=ZoneInfo("Europe/Zurich")).strftime('%Y-%m-%dT%H:%M:%S%:z')
            timekeyUTC = getUTC_min(timekeyFull)
            timetable[timekey] = {}
            timetable[timekey]["Verbrauch"] = s2rrd_splitMinGrid(timestamp=timekeyUTC, powerData=PowerDataDict["Verbrauch"])
            timetable[timekey]["Batterie"] = s2rrd_splitMinBattery(timestamp=timekeyUTC, powerData=PowerDataDict["Batterie"])
            timetable[timekey]["Wechselrichter"] = s2rrd_splitMinGeneric(timestamp=timekeyUTC, powerData=PowerDataDict["Wechselrichter"])
            allDev = 0
            for device in ["Wärmepumpe","Ladestation","SmartPlug IT","Luftentfeuchter Keller","Bewässerung Garten",
                           "Bewässerung Topf","Begleitheizung","Zusatzheizung","Weihnacht1","Weihnacht2","Waschen","Trocknen","FrigoE","FrigoK"]:
                timetable[timekey][device] = s2rrd_splitMinGeneric(timestamp=timekeyUTC, powerData=PowerDataDict[device])
                allDev += timetable[timekey][device]['summ']

            timetable[timekey]["infra"] = {}
            timetable[timekey]["infra"]["TotalBezug"] = timetable[timekey]["Wechselrichter"]['summ'] + timetable[timekey]["Verbrauch"]['summ']['iWh'] + timetable[timekey]["Batterie"]['summ']['bdWh']
            if timetable[timekey]["infra"]["TotalBezug"] == 0:
                timetable[timekey]["infra"]["TotalBezug"] = 1 / 3
            timetable[timekey]["infra"]["NettoBezug"] = timetable[timekey]["infra"]["TotalBezug"] - timetable[timekey]["Verbrauch"]['summ']['eWh'] - timetable[timekey]["Batterie"]['summ']['bcWh']
            timetable[timekey]["infra"]["Sonne%"] = timetable[timekey]["Wechselrichter"]['summ'] / timetable[timekey]["infra"]["TotalBezug"]
            timetable[timekey]["infra"]["Netz%"] = timetable[timekey]["Verbrauch"]['summ']['iWh'] / timetable[timekey]["infra"]["TotalBezug"]
            timetable[timekey]["infra"]["Battery%"] = timetable[timekey]["Batterie"]['summ']['bdWh'] / timetable[timekey]["infra"]["TotalBezug"]
            timetable[timekey]["infra"]["SoBat"] = getSplit(timetable[timekey]["Wechselrichter"]['summ'], timetable[timekey]["Batterie"]['summ']['bcWh'])
            timetable[timekey]["infra"]["NzBat"] = timetable[timekey]["Batterie"]['summ']['bcWh'] - timetable[timekey]["infra"]["SoBat"]
            timetable[timekey]["infra"]["SoNz"] = getSplit(timetable[timekey]["Wechselrichter"]['summ'] - timetable[timekey]["infra"]["SoBat"], timetable[timekey]["Verbrauch"]['summ']['eWh'])
            timetable[timekey]["infra"]["BatNz"] = timetable[timekey]["Verbrauch"]['summ']['eWh'] - timetable[timekey]["infra"]["SoNz"]
            timetable[timekey]["infra"]["rest"] = timetable[timekey]["infra"]["NettoBezug"] - allDev

            tarif = getHT(timekey)

            mintableSum['Date'] = timekey
            mintableSum['seconds'] = datetime.fromisoformat(timekeyFull).strftime('%s')
            mintableSum['PV'] += timetable[timekey]["Wechselrichter"]['summ']
            mintableSum[f'N{tarif}PV'] += timetable[timekey]["Wechselrichter"]['summ']
            mintableSum['Ni'] += timetable[timekey]["Verbrauch"]['summ']['iWh']
            mintableSum[f'N{tarif}Ni'] += timetable[timekey]["Verbrauch"]['summ']['iWh']
            mintableSum['Ne'] += timetable[timekey]["Verbrauch"]['summ']['eWh']
            mintableSum[f'N{tarif}Ne'] += timetable[timekey]["Verbrauch"]['summ']['eWh']
            mintableSum['bdWh'] += timetable[timekey]["Batterie"]['summ']['bdWh']
            mintableSum[f'N{tarif}bdWh'] += timetable[timekey]["Batterie"]['summ']['bdWh']
            mintableSum['bcWh'] += timetable[timekey]["Batterie"]['summ']['bcWh']
            mintableSum[f'N{tarif}bcWh'] += timetable[timekey]["Batterie"]['summ']['bcWh']
            mintableSum['Total_Bezug'] += timetable[timekey]["infra"]["TotalBezug"]
            mintableSum['Netto_Bezug'] += timetable[timekey]["infra"]["NettoBezug"]
            mintableSum['Sonne%'] = timetable[timekey]["infra"]["Sonne%"]
            mintableSum['Netz%'] = timetable[timekey]["infra"]["Netz%"]
            mintableSum['Batterie%'] = timetable[timekey]["infra"]["Battery%"]
            mintableSum['SoBat'] += timetable[timekey]["infra"]["SoBat"]
            mintableSum[f'N{tarif}SoBat'] += timetable[timekey]["infra"]["SoBat"]
            mintableSum['NeBat'] += timetable[timekey]["infra"]["NzBat"]
            mintableSum[f'N{tarif}NeBat'] += timetable[timekey]["infra"]["NzBat"]
            mintableSum['SoNe'] += timetable[timekey]["infra"]["SoNz"]
            mintableSum[f'N{tarif}SoNe'] += timetable[timekey]["infra"]["SoNz"]
            mintableSum['BatNe'] += timetable[timekey]["infra"]["BatNz"]
            mintableSum[f'N{tarif}BatNe'] += timetable[timekey]["infra"]["BatNz"]
            mintableSum['Rest'] += timetable[timekey]["infra"]["rest"]
            mintableSum[f'N{tarif}Rest'] += timetable[timekey]["infra"]["rest"] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}Rest'] += timetable[timekey]["infra"]["rest"] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}Rest'] += timetable[timekey]["infra"]["rest"] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['Wp'] += timetable[timekey]["Wärmepumpe"]['summ']
            mintableSum[f'N{tarif}Wp'] += timetable[timekey]["Wärmepumpe"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}Wp'] += timetable[timekey]["Wärmepumpe"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}Wp'] += timetable[timekey]["Wärmepumpe"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['La'] += timetable[timekey]["Ladestation"]['summ']
            mintableSum[f'N{tarif}La'] += timetable[timekey]["Ladestation"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}La'] += timetable[timekey]["Ladestation"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}La'] += timetable[timekey]["Ladestation"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['IT'] += timetable[timekey]["SmartPlug IT"]['summ']
            mintableSum[f'N{tarif}IT'] += timetable[timekey]["SmartPlug IT"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}IT'] += timetable[timekey]["SmartPlug IT"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}IT'] += timetable[timekey]["SmartPlug IT"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['Lk'] += timetable[timekey]["Luftentfeuchter Keller"]['summ']
            mintableSum[f'N{tarif}Lk'] += timetable[timekey]["Luftentfeuchter Keller"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}Lk'] += timetable[timekey]["Luftentfeuchter Keller"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}Lk'] += timetable[timekey]["Luftentfeuchter Keller"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['Bg'] += timetable[timekey]["Bewässerung Garten"]['summ']
            mintableSum[f'N{tarif}Bg'] += timetable[timekey]["Bewässerung Garten"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}Bg'] += timetable[timekey]["Bewässerung Garten"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}Bg'] += timetable[timekey]["Bewässerung Garten"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['Bt'] += timetable[timekey]["Bewässerung Topf"]['summ']
            mintableSum[f'N{tarif}Bt'] += timetable[timekey]["Bewässerung Topf"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}Bt'] += timetable[timekey]["Bewässerung Topf"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}Bt'] += timetable[timekey]["Bewässerung Topf"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['Bh'] += timetable[timekey]["Begleitheizung"]['summ']
            mintableSum[f'N{tarif}Bh'] += timetable[timekey]["Begleitheizung"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}Bh'] += timetable[timekey]["Begleitheizung"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}Bh'] += timetable[timekey]["Begleitheizung"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['Zh'] += timetable[timekey]["Zusatzheizung"]['summ']
            mintableSum[f'N{tarif}Zh'] += timetable[timekey]["Zusatzheizung"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}Zh'] += timetable[timekey]["Zusatzheizung"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}Zh'] += timetable[timekey]["Zusatzheizung"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['W1'] += timetable[timekey]["Weihnacht1"]['summ']
            mintableSum[f'N{tarif}W1'] += timetable[timekey]["Weihnacht1"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}W1'] += timetable[timekey]["Weihnacht1"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}W1'] += timetable[timekey]["Weihnacht1"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['W2'] += timetable[timekey]["Weihnacht2"]['summ']
            mintableSum[f'N{tarif}W2'] += timetable[timekey]["Weihnacht2"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}W2'] += timetable[timekey]["Weihnacht2"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}W2'] += timetable[timekey]["Weihnacht2"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['Wa'] += timetable[timekey]["Waschen"]['summ']
            mintableSum[f'N{tarif}Wa'] += timetable[timekey]["Waschen"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}Wa'] += timetable[timekey]["Waschen"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}Wa'] += timetable[timekey]["Waschen"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['Tr'] += timetable[timekey]["Trocknen"]['summ']
            mintableSum[f'N{tarif}Tr'] += timetable[timekey]["Trocknen"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}Tr'] += timetable[timekey]["Trocknen"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}Tr'] += timetable[timekey]["Trocknen"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['Fe'] += timetable[timekey]["FrigoE"]['summ']
            mintableSum[f'N{tarif}Fe'] += timetable[timekey]["FrigoE"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}Fe'] += timetable[timekey]["FrigoE"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}Fe'] += timetable[timekey]["FrigoE"]['summ'] * timetable[timekey]["infra"]["Battery%"]
            mintableSum['Fk'] += timetable[timekey]["FrigoK"]['summ']
            mintableSum[f'N{tarif}Fk'] += timetable[timekey]["FrigoK"]['summ'] * timetable[timekey]["infra"]["Netz%"]
            mintableSum[f'S{tarif}Fk'] += timetable[timekey]["FrigoK"]['summ'] * timetable[timekey]["infra"]["Sonne%"]
            mintableSum[f'B{tarif}Fk'] += timetable[timekey]["FrigoK"]['summ'] * timetable[timekey]["infra"]["Battery%"]

            minLine = []
            for k in mintable[0]:
                minLine.append(mintableSum[k])
            
            mintable.append(minLine)

    sDir = "data-in"
    sFile = f'{iYear}-{iMonth:02d}-{day:02d}_min.csv'
    with open(os.path.join(sDir,sFile), 'w') as outf:
        writer = csv.writer(outf, delimiter=';')
        writer.writerows(mintable)

    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(timetable)

