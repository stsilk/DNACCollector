from dnacentersdk import api
from elasticsearch import Elasticsearch
from tenable.sc import TenableSC
import datetime
import time
import pprint
import yaml
import logging
import collections
from collections Import Counter

es = '' #Elastic Connection
dnac = '' #DNAC Connection
sc = '' #Tenable Connection
DEVICELIST = []
logging.basicConfig(level=logging.INFO)

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
    logging.info("DEVICELIST: {0}".format(DEVICELIST))
    devices = dnac.devices.get_device_list()
    logging.info("Extracting IPS")
    logging.info("==oldInventory==")
    oldInventory = extractIPInfo(DEVICELIST)
    logging.info(oldInventory)
    logging.info("==newInventory==")
    newInventory = extractIPInfo(devices)
    logging.info(newInventory)
    logging.info("oldInventory: {0}".format(oldInventory))
    logging.info("newInventory: {0}".format(newInventory))
    if oldInventory == newInventory:
        logging.info("No new devices added")
        return False
    else:
        logging.info("New devices added")
        DEVICELIST = devices
        return True

init()
while True:
    result = checkNewDevices()
    if result:
        dnaIPs = []
        for i in DEVICELIST.response:
            dnaIPs.append(i['managementIpAddress'])
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
        vulnCollections = collections.defaultdict(list)
        for vuln in sc.analysis.scan(results['scanResult']['id']):
            result[vuln['ip']].append(vuln)
        combinedData = collections.defaultdict(list)
        for i in devices.response:
            combinedData[i['managementIpAddress']].append(i)
            counts = Counter(x['riskFactor'] for x in combinedData[i['managementIpAddress']][0]['vulns'])
            combinedData[i['managementIpAddress']][0]['highCount'] = counts['High']
            combinedData[i['managementIpAddress']][0]['noneCount'] = counts['None']
            combinedData[i['managementIpAddress']][0]['mediumCount'] = counts['Medium']
        for i in combinedData:
            es.index(index='dnacACAS', body=i)
    else:
        logging.info("No new devices detected")
        time.sleep(60)




