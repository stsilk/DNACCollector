from dnacentersdk import api
from elasticsearch import Elasticsearch
from tenable.sc import TenableSC
import datetime
import time
import pprint
import yaml
import logging

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
    logging.info("Extracting IPs from {0}".format(dnacResponse))
    ipList = []
    if hasattr(dnacResponse, 'response'):
        for i in dnacResponse.response:
            print(i['managementIpAddress'])
            ipList.append(i['managementIpAddress'])
        logging.info("Extracted List: {0}".format(ipList))
        return ipList
    else:
        return []
    

def checkNewDevices():
    logging.info("Checking for new devices")
    global DEVICELIST
    devices = dnac.devices.get_device_list()
    logging.info("Extracting IPS")
    logging.info(DEVICELIST)
    oldInventory = extractIPInfo(DEVICELIST)
    logging.info(devices)
    newInventory = extractIPInfo(devices)
    if oldInventory == newInventory:
        logging.info("No new devices added")
        return False
    else:
        logging.info("New devices added")
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
            logging.info('Still waiting... Status: {0} - {1}'.format(scanStatus, datetime.datetime.now()))
            time.sleep(30)
            scanStatus = sc.scan_instances.details(runningScanID)['status']
        scanEndTime = datetime.datetime.now()
        scanDuration = scanEndTime - scanStartTime
        logging.info('Scan Completed after')
    else:
        logging.info("No new devices detected")
        time.sleep(60)




