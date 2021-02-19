#!/usr/bin/python3
'''
Smart worker will do predict among week days and do train on weekends
Smart worker will be launched 7 PM every day, but because it may be delayed by previous build, 
so we are not sure exact time it starts. However, smart worker will decide prediction or training
by when it really starts. 
'''
import argparse
import json
import os
import subprocess
import urllib3
from datetime import datetime, timedelta
from pytz import timezone
import pathlib
import sys

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_root', dest='model_root', default='../model_root', help='The root folder of model.')
    parser.add_argument('--img_folder', dest='img_folder', default='../dataset', help='The input image folder path.')
    parser.add_argument('--samples', dest='sample_folder', default='../samples', help='The root folder of stock info image.')  
    parser.add_argument('--output', dest='output_root', default='../prediction', help='The root folder of prediction output.')  
    args = parser.parse_args()
    return args


def get_twse_open():
    cst = timezone('Asia/Taipei')
    yyy = datetime.now().astimezone(cst).year - 1911
    url = 'https://www.twse.com.tw/holidaySchedule/holidaySchedule?response=csv&queryYear=' + str(yyy)
    http = urllib3.PoolManager()
    res = http.request('GET', url)
    lines = res.data.decode('big5').split('\n')
    off_dates = []
    for i in range(len(lines)):
        if i < 2:
            continue
        e = lines[i].split(',')
        if len(e) < 2:
            continue
        m_d = e[1].replace('月', '_').replace('"', '').replace('日', '')
        mm = ('0' + m_d.split('_')[0]) if len(m_d.split('_')[0]) == 1 else m_d.split('_')[0] 
        dd = ('0' + m_d.split('_')[1]) if len(m_d.split('_')[1]) == 1 else m_d.split('_')[1]
        off_dates.append('%s_%s' % (mm, dd))
    return off_dates


def to_date_str(dt):
    # print(dt)
    return dt.astimezone(timezone('Asia/Taipei')).strftime('%Y_%m_%d_%H_%M_%a')


def predict(args):
    now_str = to_date_str(datetime.now())
    tomorow_str = to_date_str((datetime.now() + timedelta(days=1)))
    print(now_str)
    off_dates = get_twse_open()
    is_td = is_trade_day(off_dates, now_str) 
    print('today is trade day? ' + str(is_td))
    tomorrow_is_td = is_trade_day(off_dates, tomorow_str)
    print('tomorrow is trade day? ' + str(tomorrow_is_td))
    n_hr = now_str.split('_')[3]
    print(n_hr)     
    '''
先決定是否進行 predict    
    case 0:00 ~ 12:00 
        if today is 營業日, do predict
        if today is not 營業日, not do predict
    case 12:01 ~ 18:00, 
        do not predict (no data for prediction)
    case 18:01 ~ 23:59
        if tomorrow is 營業日, do predict
        if tomorrow is not 營業日, do not predict
    '''
    do_predict = False
    if int(n_hr) < 12 and is_td:
        do_predict = True
    if int(n_hr) >= 18 and tomorrow_is_td:
        do_predict = True
    print('do predict? ' + str(do_predict))
    if do_predict:
        proceed_predict(args)    


def proceed_predict(args):
    cmd = 'python /data_container/STOCK_PRICE_CNN/predict_all.py --model_root %s --output %s --samples %s' % (args.model_root, args.output_root, args.sample_folder)
    ret_code = subprocess.call(cmd, shell=True)
    if ret_code == 0:
        cmd = 'python /data_container/STOCK_PRICE_CNN/predict_stat.py %s' % args.output_root
        ret_code = subprocess.call(cmd, shell=True)
        if ret_code == 0:
            print('prediction statistics done.')
        else:
            print('prediction statistics fail.')
    else:
        print("Prediction Fail")



def is_trade_day(off_dates, date_str):
    wd = date_str.split('_')[5]
    print(wd)
    if wd == 'Sun' or wd == 'Sat':
        return False
    else:
        mm_dd = '_'.join(date_str.split('_')[1:3])
        print(mm_dd)
        if mm_dd in off_dates:
            return False
    return True


def train(args):
    '''
再來決定是否進行 training
    If now + 12 hours is 營業日, do not train
    else do train
如果要 train, 從 workspace 取得上次 train 的 group, 接著 train 下一個 group. 
    '''
    now_plus_12hour = to_date_str(datetime.now() + timedelta(hours=12))
    if is_trade_day(get_twse_open(), now_plus_12hour):
        do_train = False
    else:
        do_train = True
    if do_train:
        proceed_train(args)
    else:
        print('Too close to trading day, not to proceed training.')


def proceed_train(args):
    eldest_model_date = datetime.now().astimezone(timezone('Asia/Taipei'))
    eldest_group = ""
    for group_dir in os.listdir(args.model_root):
        record_path = os.path.join(args.model_root, group_dir, 'up4', 'records.json')
        if not os.path.exists(record_path):
            print('No records can be referenced, skip training %s' % group_dir)
            continue
        with open(record_path, 'r') as rfile:
            record = json.load(rfile)
            if record['recall'] < 0.8:
                print('Recall %.2f lower than 0.8, not to train %s' % (record['recall'], group_dir))
                continue
        mtime = datetime.fromtimestamp(pathlib.Path(record_path).stat().st_mtime).astimezone(timezone('Asia/Taipei'))
        if mtime < eldest_model_date:
            eldest_model_date = mtime
            eldest_group = group_dir
    print('The eldest group is %s' % eldest_group)
    cmd = 'python /data_container/STOCK_PRICE_CNN/train.py --img_folder %s/%s/up4 --output_folder %s/%s/up4 train --epoch 15' % (args.img_folder, eldest_group, args.model_root, eldest_group)
    _ = subprocess.call(cmd, shell=True)
    cmd = 'python /data_container/STOCK_PRICE_CNN/train.py --img_folder %s/%s/drop5 --output_folder %s/%s/drop5 train --epoch 15' % (args.img_folder, eldest_group, args.model_root, eldest_group)
    _ = subprocess.call(cmd, shell=True)    


def main():
    args = arg_parse()
    predict(args)
    train(args)


if __name__ == '__main__':
    main()