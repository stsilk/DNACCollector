from dnacentersdk import api
from elasticsearch import Elasticsearch
from tenable.sc import TenableSC
import datetime
import time
import pprint
import yaml

es = '' #Elastic Connection
dnac = '' #DNAC Connection
sc = '' #Tenable Connection
DEVICELIST = []

def init():
    global es
    global dnac
    global sc
    config = ''
    with open('config.yml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    es = Elasticsearch(config['elastic']['ip'],
                        http_auth=(config['elastic']['username'],config['elastic']['password']),
                        scheme="http",
                        port=9200)
    dnac = api.DNACenterAPI(base_url='https://{0}'.format(config['dnac']['ip']), 
                            username=config['dnac']['username'],
                            password=config['dnac']['password'],
                            verify=False)
    sc = TenableSC(config['tenable']['ip'])
    sc.login(config['tenable']['username'], config['tenable']['password'])

def extractIPInfo(dnacResponse):
    ipList = []
    try:
        for i in dnacResponse.response:
            ipList.append(i['managementIpAddress'])
        return ipList.sort()
    except Exception as e:
        return []

def checkNewDevices():
    global DEVICELIST
    devices = dnac.devices.get_device_list()
    oldInventory = extractIPInfo(DEVICELIST)
    newInventory = extractIPInfo(devices)
    if oldInventory == newInventory:
        print("No new devices added")
        return False
    else:
        print("New devices added")
        DEVICELIST = newInventory
        return True

init()
while True:
    result = checkNewDevices()
    if result:
        dnaIPs = []
        for i in DEVICELIST:
            dnaIPs.append(i)
        sc.asset_lists.edit('55', ips=dnaIPs)
        results = sc.scans.launch('39')
        scanStartTime = datetime.datetime.now()
        runningScanID = results['scanResult']['id']
        scanStatus = sc.scan_instances.details(runningScanID)['status']
        while scanStatus != 'Completed':
            print('Still waiting... Status: {0} - {1}'.format(scanStatus, datetime.datetime.now()))
            time.sleep(30)
            scanStatus = sc.scan_instances.details(runningScanID)['status']
        scanEndTime = datetime.datetime.now()
        scanDuration = scanEndTime - scanStartTime
        print('Scan Completed after')
    else:
        print("No new devices detected")
        time.sleep(60)




