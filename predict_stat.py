#!/usr/bin/python3
import os
import sys
import numpy as np
import pandas as pd
import datetime
from pytz import timezone



def by_group(df):
    df['up4_gt'] = (((df['up4'] * 2 - 1) * df['up4_predicted'] + 1) / 2).astype('uint8')
    df['drop5_gt'] = (((df['drop5'] * 2 - 1) * df['drop5_predicted'] + 1) / 2).astype('uint8')
    # df.to_excel('all_predicts.xls')
    by_g = df.groupby(by=['group'])
    row_list = []
    for g, g_df in by_g:
        # print('group:' + g)
        up4_tp = len(g_df[(g_df.up4 == 1) & (g_df.up4_gt == 1)])
        up4_recall = up4_tp / g_df['up4_gt'].sum()
        up4_precision = up4_tp / g_df['up4'].sum()
        drop5_tp = len(g_df[(g_df.drop5 == 1) & (g_df.drop5_gt == 1)])
        drop5_recall = drop5_tp / g_df['drop5_gt'].sum()
        drop5_precision = drop5_tp / g_df['drop5'].sum()
        row_list.append(
            {'group': g,
             'r_up4': up4_recall, 
             'p_up4': up4_precision,
             'r_drop5': drop5_recall,
             'p_drop5': drop5_precision})
        print('%s r_up4: %.2f, p_up4: %.2f, r_drop5: %.2f, p_drop5: %.2f ' % (g, up4_recall, up4_precision, drop5_recall, drop5_precision))
    return pd.DataFrame(row_list)

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
        # print('group: %s, date: %s' % (group_name, date_str))
        df = pd.read_csv(data_path, index_col=None, header=0)
        if len(df[df['up4_predicted'] == 0]) == len(df):
            print('Yet ground truth, excluded.')
            continue
        df['group'] = group_name
        dfs.append(df)
    stat_df = pd.concat(dfs, axis=0, ignore_index=True)

    today_str = datetime.datetime.now().astimezone(cst).strftime('%Y_%m_%d')
    # statics by date
    # statics by group
    result_by_group = by_group(stat_df)
    result_by_group.to_excel(os.path.join(pred_folder, 'by_group_predict_stat_%s.xls' % today_str), index=False)
    # statics by trend
    # statics by raw
    #print(stat_df)
    



if __name__ == '__main__':
    main()