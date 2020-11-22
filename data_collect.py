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


def query_stock(id, stock_folder):
    base_data = twstock.codes[id]
    # print(base_data)
    # print(start)
    stock = Stock(id, False)
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
    while (12 * the_year + the_mon) <= (12 * now_year + now_mon):
        file_path = os.path.join(stock_folder, '%s_%d_%02d.csv' % (id, the_year, the_mon))
        if not os.path.exists(file_path) or (the_year == now_year and the_mon == now_mon):
            print('fetching %s(%s) of %d/%d' % (id, base_data.name, the_year, the_mon))
            lines = ['date,capacity,turnover,open,high,low,close,change,transaction']
            start_time = time.time()
            a_month = stock.fetch(the_year, the_mon)
            for a_day in a_month:
                lines.append('%s,%ld,%ld,%.2f,%.2f,%.2f,%.2f,%.2f,%ld' %\
                    (a_day.date.strftime('%Y_%m_%d'),\
                    a_day.capacity,\
                    a_day.turnover,\
                    a_day.open,\
                    a_day.high,\
                    a_day.low,\
                    a_day.close,\
                    a_day.change,\
                    a_day.transaction))
                # date=datetime.datetime(2010, 1, 4, 0, 0)
                # capacity=6862825
                # turnover=295967924
                # open=43.6
                # high=43.9
                # low=42.85
                # close=42.95
                # change=-0.65
                # transaction=2739
            with open(file_path, 'w') as ofile:
                ofile.write('\n'.join(lines))
            # df = pd.read_csv(file_path, header=0)
            # print(df)
            elapse_time = time.time() - start_time
            print('elapse seconds: %f' % elapse_time)
            # sys.exit(0)
        if (the_mon < 12):
            the_mon += 1
        else:
            the_mon = 1
            the_year += 1
        # sys.exit(0)


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--groups', nargs='+', type=str, default=['食品工業'], help='the groups of stock:' + ','.join(all_group_list))
    parser.add_argument('--output', type=str, default=os.getcwd(), help='the root folder path of all the output')
    opt = parser.parse_args()
    return opt


def main():
    opt = parse_arg()
    print(all_group_list)
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
            query_stock(info.code, stock_folder)
    
    # sys.exit(0)
    # query_stock('1216')  


if __name__ == '__main__':
    main()
