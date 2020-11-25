#!/home/user/anaconda3/bin/python
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import twstock
import os
from datetime import date, datetime, timedelta


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
    return stock_df


def incontinuous_month(df):
    year_mon = df['date'].\
        apply(lambda x:(
            int(x.split('_')[0]) - 2010) * 12 + int(x.split('_')[1])).\
        drop_duplicates()
    the_range = year_mon.max() - year_mon.min() + 1
    print(
        '# of different months: %d, from %d/%02d to %d/%02d' %\
        (len(year_mon),\
         2010 + year_mon.min() // 12, year_mon.min() % 12,
         2010 + year_mon.max() // 12, year_mon.max() % 12))
    if the_range != len(year_mon):
        return True
    # print(year_mon)
    return False


def not_long_enough(df):
    lastd = df['date'].max()
    print(lastd)
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
    return False


def under_liquidity(df):
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


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--groups', nargs='+', type=str, default=['食品工業'], help='the groups of stock:' + ','.join(all_group_list))
    parser.add_argument('--rawdata', type=str, default=os.getcwd(), help='the root folder path of all the output')
    opt = parser.parse_args()
    return opt


def main():
    opt = parse_arg()
    stock_df = load_stock('1216', opt.rawdata)
    print(stock_df)
    qualified, message = data_qualification(stock_df)
    '''
    for group in opt.groups:
        stock_list = []
        # collect stock id list of group
        for key in twstock.codes:
            if twstock.codes[key].group == group and\
                    twstock.codes[key].market == '上市':
                stock_list.append(twstock.codes[key])
    '''

if __name__ == '__main__':
    main()