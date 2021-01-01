#!/home/user/anaconda3/bin/python
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import twstock
import os
from datetime import date, datetime, timedelta
import sys
import utils
import time
import json
import cv2


all_group_list = []
for key in twstock.codes:
    if twstock.codes[key].group not in all_group_list:
        all_group_list.append(twstock.codes[key].group)

def load_stock(stock_id, data_folder):
    stock_folder_path = os.path.join(data_folder, stock_id)
    assert os.path.exists(stock_folder_path), 'Invalid stock folder path: %s' % stock_folder_path
    dfs = []
    for file in sorted(os.listdir(stock_folder_path)):
        if not file.endswith('.csv'):
            continue
        df = pd.read_csv(os.path.join(stock_folder_path, file), index_col=None, header=0)
        dfs.append(df)
    stock_df = pd.concat(dfs, axis=0, ignore_index=True)
    stock_df['week'] = stock_df['date'].apply(utils.date_to_week)
    stock_df['month'] = stock_df['date'].apply(lambda x: x[:7])
    print(stock_df.head())
    return stock_df


def incontinuous_month(df):
    year_mon = df['date'].\
        apply(lambda x:(
            int(x.split('_')[0]) - 2010) * 12 + int(x.split('_')[1])).\
        drop_duplicates()
    the_range = year_mon.max() - year_mon.min() + 1
    if year_mon.min() % 12 == 0:
        mon_of_min_ym = 12
        year_of_min_ym = 2010 + (year_mon.min() // 12) - 1
    else:
        mon_of_min_ym = year_mon.min() % 12
        year_of_min_ym = 2010 + (year_mon.min() // 12) 
    if year_mon.max() % 12 == 0:
        mon_of_max_ym = 12
        year_of_max_ym = 2010 + (year_mon.max() // 12) - 1
    else:
        mon_of_max_ym = year_mon.max() % 12
        year_of_max_ym = 2010 + (year_mon.max() // 12)
    print(
        '# of different months: %d, from %d/%02d to %d/%02d' %\
        (len(year_mon),\
         year_of_min_ym, mon_of_min_ym,
         year_of_max_ym, mon_of_max_ym))
    if the_range != len(year_mon):
        return True
    # print(year_mon)
    return False


def not_long_enough(df):
    lastd = df['date'].max()
    # print(lastd)
    d = datetime.strptime(lastd, '%Y_%m_%d')
    first_day_of_previous_month = (d.replace(day=1) - timedelta(days=1)).replace(day=1)
    three_years_ago = first_day_of_previous_month.replace(year=first_day_of_previous_month.year - 3)
    # print(first_day_of_previous_month.strftime('%Y_%m_%d'))
    # print(three_years_ago.strftime('%Y_%m_%d'))
    df = df[df['date'] <= three_years_ago.strftime('%Y_%m_%d')]
    print('%d samples can be generated.' % len(df))
    if len(df) == 0:
        return True
    return False


def over_price_range(df):
    min_p = df['close'].min()
    min_date = df[df['close'] == min_p]['date'].iloc[0]
    max_p = df['close'].max()
    max_date = df[df['close'] == max_p]['date'].iloc[0]
    print(
        'price: bottom = %.2f (%s), top = %.2f (%s)' %\
        (min_p, min_date, max_p, max_date))
    if min_p < 10.0 or max_p > 600.0:
        return True    
    return False


def under_liquidity(df):
    mean_trans = df['transaction'].mean()
    print('mean transaction = %.1f' % mean_trans)
    if mean_trans < 20.0:
        return True
    return False


def data_qualification(df):
    if incontinuous_month(df):
        return False, 'Some months missing.'
    if not_long_enough(df):
        return False, 'Duration not long enough for one sample.'
    if over_price_range(df):
        return False, 'Not in price range.'
    if under_liquidity(df):
        return False, 'Average transaction under threshold.'
    qualified = True
    message = 'OK'

    return qualified, message


def ground_truth(df, the_date, ofile_path):
    sample_data = {'GT': [0, 0]}
    # ground truth 0: if ever 4% price-up in coming month
    # ground truth 1: if ever 5% price-drop in coming month
    next_mon_df = df[df['date'].between(utils.nextday(the_date), utils.day_next_month(the_date))]
    # print(next_mon_df)
    base_price = df[df['date'] == the_date].iloc[0]['close']
    # print(base_price)
    up_4 = next_mon_df[next_mon_df['close'] >= base_price * 1.04]
    drop_5 = next_mon_df[next_mon_df['close'] <= base_price * 0.95]
    if len(up_4) > 0:
        sample_data['GT'][0] = 1
        sample_data['up_4_date'] = up_4['date'].tolist()
        sample_data['up_4_price'] = up_4['close'].tolist()
    if len(drop_5) > 0:
        sample_data['GT'][1] = 1
        sample_data['drop_5_date'] = drop_5['date'].tolist()
        sample_data['drop_5_price'] = drop_5['close'].tolist()
    # save and return the ground truth      
    with open(os.path.join(ofile_path, 'gt.json'), 'w') as jfile:
        jfile.write(json.dumps(sample_data, indent=4))
    return sample_data


def sample(df, the_date, ofile_path, boundary):
    if not os.path.exists(ofile_path):
        os.mkdir(ofile_path)
    dirname = os.path.basename(ofile_path)
    final_png_path = os.path.join(ofile_path, '%s.png' % dirname)
    if (os.path.exists(final_png_path)): # the final png is there, skip
        return
    # daily capacity, high, low, close among last 60 days
    the_latest_date = df['date'].max()
    if the_date = utils.nextday(the_latest_date):
        base_index = df.index[df['date'] == the_latest_date].to_list()[0] + 1
    else:
        base_index = df.index[df['date'] == the_date].to_list()[0]
    recent_60d = df.iloc[base_index - 60: base_index]
    recent_60d.reset_index(drop=True, inplace=True)
    # print(df.iloc[base_index - 60: base_index])
    # weekly capacity, high, low, close among last 52 weeks
    curr_week = df[df['date'] == the_date]['week'].iloc[0]
    week_prev_year = utils.week_prev_year(the_date)
    recent_52w = df[(df['week'] <= curr_week) & (df['week'] >= week_prev_year) & (df['date'] < the_date)]
    recent_52w = recent_52w[['week', 'close', 'transaction']].copy()
    recent_52w = recent_52w.groupby(by=['week']).mean()
    recent_52w.reset_index(drop=True, inplace=True)
    # print(recent_52w)
    # monthly capacity, high, low, close amont last 36 months
    curr_mon = the_date[:7]
    mon_3_years_ago = utils.mon_3_years_ago(the_date) 
    recent_36m = df[(df['month'] <= curr_mon) & (df['month'] >= mon_3_years_ago) & (df['date'] < the_date)]
    recent_36m = recent_36m[['month', 'close', 'transaction']].copy()
    recent_36m = recent_36m.groupby(by=['month']).mean()
    recent_36m.reset_index(drop=True, inplace=True)
    plot(ofile_path, recent_60d, recent_52w, recent_36m, boundary)


def plot_for_df(ofile_path, df, boundary, sequence, xlabel):
    fig, ax = plt.subplots()
    ax.plot(df.index, df.close, color='red', marker='o')
    ax.set_ylim(boundary[1]['price'], boundary[0]['price'])
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Price', color='red')
    ax2 = ax.twinx()
    ax2.plot(df.index, df.transaction, color='blue', marker='o')
    ax2.set_ylabel('Transaction', color='blue')
    ax2.set_ylim(boundary[1]['transaction'], boundary[0]['transaction'])
    dirname = os.path.basename(ofile_path)
    fig.savefig(os.path.join(ofile_path, '%s.%d.png' % (dirname, sequence)))
    plt.close('all')


def plot(ofile_path, recent_60d, recent_52w, recent_36m, boundary):
    
    ## 1: <recent_60d>
    plot_for_df(ofile_path, recent_60d, boundary, 1, 'Day')
    ## 2: <recent_52w>
    plot_for_df(ofile_path, recent_52w, boundary, 2, 'Week')
    ## 3: <recent_36m>
    plot_for_df(ofile_path, recent_36m, boundary, 3, 'Month')
    

def concat_png(id, sample_date, ofile_path):
    dirname = os.path.basename(ofile_path)
    final_png = '%s.png' % dirname
    if os.path.exists(os.path.join(ofile_path, final_png)):
        print('skip concatenated, %s already there.' % final_png)
    else:
        img_list = []
        for i in range(3):
            png_path = os.path.join(ofile_path, '%s.%d.png' % (dirname, i+1))
            if not os.path.exists(png_path):
                return
            else:
                img_list.append(cv2.imread(png_path))
                os.remove(png_path)
        final_img = cv2.vconcat(img_list)
        cv2.imwrite(os.path.join(ofile_path, final_png), final_img)


def gen_samples(df, id, output_folder):
    start = time.time()
    gt_df = pd.DataFrame(columns=['id', 'date', 'up4', 'drop5'])
    min_start = utils.day_next3_year(df['date'].min())
    train_start = df[df['date'] >= min_start]['date'].min()
    train_end = utils.day_prev_month(df['date'].max())
    print('Generate sample from %s to %s' % (train_start, train_end))
    sample_date = train_start
    the_max = {
        'price': df['high'].max(), 
        'transaction': df['transaction'].max(),
        'capacity': df['capacity'].max()}
    the_min = {
        'price': df['low'].min(),
        'transaction': df['transaction'].min(),
        'capacity': df['capacity'].min()
    }
    boundary = [the_max, the_min]
    print('price:%.2f ~ %.2f' % (boundary[1]['price'], boundary[0]['price']))
    while sample_date <= train_end:
        if len(df[df['date'] == sample_date]) == 1:
            ofile_path = os.path.join(output_folder, '%s_%s' % (id, sample_date))
            gt_file = os.path.join(ofile_path, 'gt.json')
            if not os.path.exists(gt_file):
                print('sampling %s' % sample_date)
                sample(df, sample_date, ofile_path, boundary)
                concat_png(id, sample_date, ofile_path)
                gt = ground_truth(df, sample_date, ofile_path)
                if gt['GT'][0] == 1:
                    print('up 4% dates:', ' '.join(gt['up_4_date']))
                if gt['GT'][1] == 1:
                    print('drop 5% dates:', ' '.join(gt['drop_5_date']))                
            else:
                with open(gt_file, 'r') as jfile:
                    gt = json.load(jfile)
                # print('%s has been sampled, skip.' % sample_date)
            gt_df.loc[len(gt_df)] = [id, sample_date, gt['GT'][0], gt['GT'][1]]
            # concate all 3 PNGs into one
        sample_date = utils.nextday(sample_date)
    gt_df.to_csv(os.path.join(output_folder, '%s.csv' % id), index=False)
    up4 = len(gt_df[gt_df['up4'] == 1]) / len(gt_df)
    drop5 = len(gt_df[gt_df['drop5'] == 1]) / len(gt_df)
    print('%s(%s) up 4%%: %.2f, drop 5%%: %.2f' % (id, twstock.codes[id].name, up4, drop5))
    elapse_time = time.time() - start
    print('Elapse %.2f seconds for generating samples for %s(%s)' % (elapse_time, id, twstock.codes[id].name))
    ### generate png only (yet ground truth) ####
    while sample_date <= df['date'].max():
        if len(df[df['date'] == sample_date]) == 1:
            print('sampling for yet ground truth %s' % sample_date)
            ofile_path = os.path.join(output_folder, '%s_%s' % (id, sample_date))
            sample(df, sample_date, ofile_path, boundary)
            concat_png(id, sample_date, ofile_path)
        sample_date = utils.nextday(sample_date)
    # predict one day
    print('sampling on latest data to predict one day %s' % sample_date)
    sample(df, sample_date, ofile_path, boundary)
    concat_png(id, sample_date, ofile_path)

def gen_samples_for_stock(id, opt):
    rawdata_folder = opt.rawdata
    output_folder = opt.output
    print('%s (%s) load raw data into dataframe ...' % (id, twstock.codes[id].name))
    stock_df = load_stock(id, rawdata_folder)
    print('%s (%s) qualifying data ...' % (id, twstock.codes[id].name))
    qualified, message = data_qualification(stock_df)
    print('Result:%s' % message)
    print('%s (%s) generating samples ...' % (id, twstock.codes[id].name))
    if qualified:
        gen_samples(stock_df, id, output_folder)
    else:
        print('stock %s (%s) not qualified, skip sampling.' % (id, twstock.codes[id].name))
    

def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--groups', nargs='+', type=str, default=['食品工業'], help='the groups of stock:' + ','.join(all_group_list))
    parser.add_argument('--rawdata', type=str, default=os.getcwd(), help='the root folder path of all the output')
    parser.add_argument('--output', type=str, default=os.path.join(os.getcwd(), 'samples'), help='the folder path of generated samples')
    opt = parser.parse_args()
    return opt


def sample_for_group(stock_list, opt):
    for id in stock_list:
        # print(id)
        gen_samples_for_stock(id, opt)


def main():
    opt = parse_arg()
    # gen_samples_for_stock('1201', opt)
    # print(stock_df)
    for group in opt.groups:
        stock_list = []
        # collect stock id list of group
        for key in twstock.codes.keys():
            if twstock.codes[key].group == group and\
                    twstock.codes[key].market == '上市':
                stock_list.append(key)
        print('### %s ###' % group)
        sample_for_group(stock_list, opt)
    

if __name__ == '__main__':
    main()