# dnaCollector

Docker container that will
1. Scan DNAC inventory for any changes.
2. When a new inventory item is found add to Tenable inventory and trigger a scan
3. Parse scan results and upload to Elasticsearch instance
