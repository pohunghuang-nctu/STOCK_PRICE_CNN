#!/home/user/anaconda3/bin/python
import requests
from twstock import Stock, proxy
import twstock
import sys
import time
from datetime import datetime
import pandas as pd
import random
import argparse
import os
from twse import twse
import json


proxy_list = [
    {'http': 'http://5.189.133.231:80'},
    {'http': 'http://173.212.202.65:80'},
    {'http': 'http://221.180.170.104:8080'},
    {'http': 'http://82.200.233.4:3128'},
    # {'http': 'http://159.255.188.134:41258'},
    {'http': 'http://169.57.1.84:80'},
    {'http': 'http://180.179.98.22:3128'},
    {'http': 'http://169.57.1.85:8123'},
    {'http': 'http://75.151.213.85:8080'},
    {'http': 'http://169.57.1.84:8123'},
    {'http': 'http://169.57.157.146:8123'},
    {'http': 'http://88.99.10.251:1080'},
    {'http': 'http://186.233.104.164:8080'},
    {'http': 'http://103.21.160.10:35101'},
    {'http': 'http://169.57.157.148:8123'},
]
random.shuffle(proxy_list)
rrpr = proxy.RoundRobinProxiesProvider(proxy_list)
# twstock.proxy.configure_proxy_provider(rrpr)
all_group_list = []
for key in twstock.codes:
    if twstock.codes[key].group not in all_group_list:
        all_group_list.append(twstock.codes[key].group)


def next_month(the_year, the_mon):
    if (the_mon < 12):
        ret_mon = the_mon + 1
        ret_year = the_year
    else:
        ret_mon = 1
        ret_year = the_year + 1
    return ret_year, ret_mon    


def query_stock(twse, id, stock_folder):
    # prepare list for months which unable to query
    invalid_mon_fpath = os.path.join(stock_folder, 'invalid.json')
    if os.path.exists(invalid_mon_fpath):
        with open(invalid_mon_fpath, 'r') as invmon_file:
            invalid_month = json.load(invmon_file)
    else:
        invalid_month = []
    # prepare list for days that we have updated data for
    # avoiding read again
    sfile_path = os.path.join(stock_folder, 'status.json')
    if os.path.exists(sfile_path):
        with open(sfile_path, 'r') as stat_file:
            query_status = json.load(stat_file)
    else:
        query_status = []
    base_data = twstock.codes[id]
    # print(base_data)
    # print(start)
    # stock = Stock(id, False)
    start_year = base_data.start[:4]
    start_mon = base_data.start[5:7]
    print('start year: %s, start_mon %s' % (start_year, start_mon))
    now_year = datetime.today().year
    now_mon = datetime.today().month
    now_day = datetime.today().day
    if (12 * int(start_year) + int(start_mon)) < (12 * 2010 + 1):
        the_year = 2010
        the_mon = 1
    else:
        the_year = int(start_year)
        the_mon = int(start_mon)
    prev = 0.0
    while (12 * the_year + the_mon) <= (12 * now_year + now_mon):
        if '%d_%02d' % (the_year, the_mon) in invalid_month:
            print('Not exist data for %s: %d/%02d' % (id, the_year, the_mon))
            the_year, the_mon = next_month(the_year, the_mon)
            continue
        file_path = os.path.join(stock_folder, '%s_%d_%02d.csv' % (id, the_year, the_mon))
        if not os.path.exists(file_path) or (the_year == now_year and the_mon == now_mon):
            if the_year == now_year and the_mon == now_mon:
                if '%d_%02d_%02d' % (now_year, now_mon, now_day) in query_status:
                    print('We have checked %s:%d_%02d today, skip.' % (id, the_year, the_mon))
                    break
            print('fetching %s(%s) of %d/%d' % (id, base_data.name, the_year, the_mon))
            lines = ['date,capacity,turnover,open,high,low,close,change,transaction']
            while (time.time() - prev) < 5.0:
                time.sleep(0.5)
            start_time = time.time()
            prev = start_time
            # a_month = stock.fetch(the_year, the_mon)
            a_month, message = twse.get_month(id, the_year, the_mon)
            if message != 'OK':
                if message == '很抱歉，沒有符合條件的資料!':
                    invalid_month.append('%d_%02d' % (the_year, the_mon))
                print('no data this month, go to next month')
            else:
                for a_day in a_month:
                    try:
                        lines.append('%s,%ld,%ld,%.2f,%.2f,%.2f,%.2f,%.2f,%ld' %\
                            (a_day['date'],\
                            a_day['capacity'],\
                            a_day['turnover'],\
                            a_day['open'],\
                            a_day['high'],\
                            a_day['low'],\
                            a_day['close'],\
                            a_day['change'],\
                            a_day['transaction']))
                    except Exception:
                        print('Error:')
                        print(a_day)
                with open(file_path, 'w') as ofile:
                    ofile.write('\n'.join(lines))
                if the_year == now_year and the_mon == now_mon:
                    query_status.append('%d_%02d_%02d' % (now_year, now_mon, now_day))
                    with open(os.path.join(stock_folder, 'status.json'), 'w') as stat_file:
                        stat_file.write(json.dumps(query_status, indent=4))    
            elapse_time = time.time() - start_time
            print('elapse seconds: %f' % elapse_time)
        if (the_mon < 12):
            the_mon += 1
        else:
            the_mon = 1
            the_year += 1
    with open(invalid_mon_fpath, 'w') as invmon_file:
        invmon_file.write(json.dumps(invalid_month, indent=4))


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--groups', nargs='+', type=str, default=['食品工業'], help='the groups of stock:' + ','.join(all_group_list))
    parser.add_argument('--output', type=str, default=os.getcwd(), help='the root folder path of all the output')
    opt = parser.parse_args()
    return opt


def main():
    opt = parse_arg()
    print(all_group_list)
    t = twse()
    for group in opt.groups:
        stock_list = []
        # collect stock id list of group
        for key in twstock.codes:
            if twstock.codes[key].group == group and\
                    twstock.codes[key].market == '上市':
                stock_list.append(twstock.codes[key])
        for info in stock_list:
            stock_folder = os.path.join(opt.output, info.code)
            if not os.path.exists(stock_folder):
                os.mkdir(stock_folder)
            query_stock(t, info.code, stock_folder)
            time.sleep(3.0)
    t.close()
    # sys.exit(0)
    # query_stock('1216')  


if __name__ == '__main__':
    main()
