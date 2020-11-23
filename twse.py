#!/home/user/anaconda3/bin/python
from http.client import HTTPSConnection
import json
import twstock
import os
import time
from datetime import datetime


TWSE_HOST = 'www.twse.com.tw'
QUERY_URL = '/exchangeReport/STOCK_DAY'
STOCKID = [
    '1213', '1215', '1216', '1217',
    '1218', '1219', '1220', '1225'
]

class twse(object):
    def __init__(self):
        self.conn = HTTPSConnection(TWSE_HOST)
        self.conn.connect()

    def orgnize_data(self, raw_data):
        data = []
        for entry in raw_data:
            a_day = {}
            invalid = False
            for i in range(9):
                if entry[i] == '--':
                    invalid = True
                    break
            if invalid:
                continue
            # entry[0]: date
            seg = entry[0].split('/')
            a_day['date'] = '%d_%s_%s' % (int(seg[0]) + 1911, seg[1], seg[2])
            a_day['capacity'] = int(entry[1].replace(',', ''))
            a_day['turnover'] = int(entry[1].replace(',', ''))
            a_day['open'] = float(entry[3].replace(',', ''))
            a_day['high'] = float(entry[3].replace(',', ''))
            a_day['low'] = float(entry[3].replace(',', ''))
            a_day['close'] = float(entry[3].replace(',', ''))
            a_day['change'] = float(0.0 if entry[7].replace(',', '') == 'X0.00' else entry[7].replace(',', ''))
            a_day['transaction'] = int(entry[8].replace(',', ''))
            data.append(a_day)
        return data

    def get_month(self, id, year, month):
        url = '%s?date=%d%02d01&stockNo=%s' %\
            (QUERY_URL, year, month, id)
        # print(url)
        retry = 0
        while True:
            self.conn.request('GET', url)
            resp = self.conn.getresponse()
            if resp.status == 200:
                break
            else:
                if retry >= 5:
                    print('Fatal Error: retry > 5')
                    return []
                print(resp.status, resp.reason)
                retry += 1
                time.sleep(5.0)
                print('retry %d' % retry)
        # headers = resp.getheaders()
        # for header in headers:
        #     print(header)
        data = json.loads(resp.read().decode('utf-8'))
        if data['stat'] == 'OK':
            # print(data['fields'])
            return self.orgnize_data(data['data'])
        else:
            print('error: %s' % json.dumps(data, indent=4))
            return []

    def close(self):
        self.conn.close()


def query_stock(twse, id):
    base_data = twstock.codes[id]
    start_year = base_data.start[:4]
    start_mon = base_data.start[5:7]
    print('start year: %s, start_mon %s' % (start_year, start_mon))
    now_year = datetime.today().year
    now_mon = datetime.today().month
    if (12 * int(start_year) + int(start_mon)) < (12 * 2010 + 1):
        the_year = 2010
        the_mon = 1
    else:
        the_year = int(start_year)
        the_mon = int(start_mon)
    prev = 0.0
    while (12 * the_year + the_mon) <= (12 * now_year + now_mon):
        file_path = os.path.join(os.getcwd(), '%s_%d_%02d.json' % (id, the_year, the_mon))
        while (time.time() - prev) < 5.0:
            time.sleep(0.5)
        start_time = time.time()
        prev = start_time
        a_month = twse.get_month(id, the_year, the_mon)
        with open(file_path, 'w') as ofile:
            ofile.write(json.dumps(a_month, indent=4))
        elapse_time = time.time() - start_time
        print('elapse seconds: %.3f' % elapse_time)
        if (the_mon < 12):
            the_mon += 1
        else:
            the_mon = 1
            the_year += 1


def main():
    t = twse()
    for id in STOCKID:
        query_stock(t, id)
    # data = t.get_month('1203', 2018, 7)
    # print(json.dumps(data, indent=4))
    # t.get_month('1210', 2020, 11)
    t.close()


if __name__ == '__main__':
    main()

