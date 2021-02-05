#!/usr/bin/python3
import os
import sys
import numpy as np
import pandas as pd
import datetime
from pytz import timezone


def main():
    pred_folder = sys.argv[1]
    predict_dates = []
    cst = timezone('Asia/Taipei')
    for i in range(31, 61):
        predict_dates.append((datetime.datetime.now() + datetime.timedelta(days=(0 - i))).astimezone(cst).strftime('%Y_%m_%d'))
    dfs = []
    for dir in os.listdir(pred_folder):
        if not os.path.isdir(os.path.join(pred_folder, dir)):
            continue
        data_path = os.path.join(pred_folder, dir, 'predictions.csv')
        if not os.path.exists(data_path):
            continue
        group_name = dir.split('_')[0]
        date_str = '_'.join(dir.split('_')[1:])
        if date_str not in predict_dates:
            continue
        print('group: %s, date: %s' % (group_name, date_str))
        df = pd.read_csv(data_path, index_col=None, header=0)
        if len(df[df['up4_predicted'] == 0]) == len(df):
            print('Yet ground truth, excluded.')
            continue
        df['group'] = group_name
        dfs.append(df)
    stat_df = pd.concat(dfs, axis=0, ignore_index=True)

    # statics by date
    # statics by group
    # statics by trend
    # statics by raw
    print(stat_df)
    



if __name__ == '__main__':
    main()