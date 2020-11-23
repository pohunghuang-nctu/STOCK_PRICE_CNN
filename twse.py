#!/home/user/anaconda3/bin/python
from http.client import HTTPSConnection
import json


TWSE_HOST = 'www.twse.com.tw'
QUERY_URL = '/exchangeReport/STOCK_DAY'

class twse(object):
    def __init__(self):
        self.conn = HTTPSConnection(TWSE_HOST)
        self.conn.connect()

    def get_month(self, id, year, month):
        url = '%s?date=%d%02d01&stockNo=%s' %\
            (QUERY_URL, year, month, id)
        print(url)
        self.conn.request('GET', url)
        resp = self.conn.getresponse()
        print(resp.status, resp.reason)
        headers = resp.getheaders()
        for header in headers:
            print(header)
        data = json.loads(resp.read().decode('utf-8'))
        print(data)

    def close(self):
        self.conn.close()


def main():
    t = twse()
    t.get_month('1216', 2020, 11)
    # t.get_month('1210', 2020, 11)
    t.close()


if __name__ == '__main__':
    main()

