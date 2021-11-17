from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxDBObject():
    def __init__(self, token, url):
        self.token = token
        self.client = InfluxDBClient(url=url, token=self.token)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)