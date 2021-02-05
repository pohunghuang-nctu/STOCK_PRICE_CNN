#!/usr/bin/python3
#from predict import *
import argparse
import json
import os
import subprocess
import datetime
import sys
import pandas
import utils
from pytz import timezone


ACC_THRESHOLD = 0.84

def predict_all_arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_root', dest='model_root', default='../model_root', help='The root folder of model.')
    parser.add_argument('--samples', dest='sample_folder', default='../samples', help='The root folder of stock info image.')  
    parser.add_argument('--output', dest='output_root', default='../predictions', help='The root folder of prediction output.')  
    args = parser.parse_args()
    return args

def predict_all_main():
    args = predict_all_arg_parse()
    m_root = args.model_root
    pred_groups = []
    for dir in os.listdir(m_root):
        if os.path.isdir(os.path.join(m_root, dir)):
            up4_json = os.path.join(m_root, dir, 'up4', 'records.json')
            if not os.path.exists(up4_json):
                continue
            with open(up4_json, 'r') as jup4:
                r_up4 = json.load(jup4)
            drop5_json = os.path.join(m_root, dir, 'drop5', 'records.json')
            if not os.path.exists(drop5_json):
                continue
            with open(drop5_json, 'r') as jdrop5:
                r_drop5 = json.load(jdrop5)
            if r_up4['recall'] > ACC_THRESHOLD and r_up4['precision'] > ACC_THRESHOLD and \
                    r_drop5['recall'] > ACC_THRESHOLD and r_drop5['precision'] > ACC_THRESHOLD:
                pred_groups.append(dir) 
    predict_dates = []
    cst = timezone('Asia/Taipei')
    if datetime.datetime.now().astimezone(cst).hour < 13:
        predict_dates.append(datetime.datetime.now().astimezone(cst).strftime('%Y_%m_%d'))
    else:
        predict_dates.append((datetime.datetime.now() + datetime.timedelta(days=1)).astimezone(cst).strftime('%Y_%m_%d'))
    for i in range(31, 61):
        predict_dates.append((datetime.datetime.now() + datetime.timedelta(days=(0 - i))).astimezone(cst).strftime('%Y_%m_%d'))
    for date_str in predict_dates:
        for g in pred_groups:
            pred_script = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'predict.py')
            cmd = ['python', pred_script, g, date_str, '--model_root', args.model_root, '--samples', args.sample_folder, '--output', args.output_root]
            print(' '.join(cmd))
            subprocess.call(' '.join(cmd), shell=True)

      
        

if __name__ == '__main__':
    predict_all_main()