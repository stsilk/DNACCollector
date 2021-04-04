from dnacentersdk import api
from elasticsearch import Elasticsearch
from tenable.sc import TenableSC
import datetime
import time

es = '' #Elastic Connection
dnac = '' #DNAC Connection
sc = '' #Tenable Connection
DEVICELIST = []

def init():
    global es
    global dnac
    global sc
    es = Elasticsearch(['10.0.60.80'],
                        http_auth=('elastic','asdf1234ASDF!@#$'),
                        scheme="http",
                        port=9200)
    dnac = api.DNACenterAPI(base_url='https://192.168.15.91', 
                            username='steven.silk.dadm',
                            password='asdf1234ASDF!@#$',
                            verify=False)
    sc = TenableSC('192.168.15.109')
    sc.login('scanuser', '1qaz2wsx#EDC$RFV')

def checkNewDevices():
    global DEVICELIST
    devices = dnac.devices.get_device_list()
    if DEVICELIST == devices:
        print("No new devices added")
        return False
    else:
        print("New device detected")
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
            print('Still waiting... Status: {0} - {1}'.format(scanStatus, datetime.datetime.now()))
            time.sleep(30)
            scanStatus = sc.scan_instances.details(runningScanID)['status']
       
        scanEndTime = datetime.datetime.now()
        scanDuration = scanEndTime - scanStartTime
        print('Scan Completed after')
    else:
        print("No new devices detected")
        time.sleep(60)




