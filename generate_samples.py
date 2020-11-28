#!/home/user/anaconda3/bin/python
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import twstock
import os
from datetime import date, datetime, timedelta
import sys
import utils


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


def sample(df, the_date, ofile_path, boundary):
    os.mkdir(ofile_path)
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
        sample_data['up_4_date'] = up_4['date']
        sample_data['up_4_price'] = up_4['close']
    if len(drop_5) > 0:
        sample_data['GT'][1] = 1
        sample_data['drop_5_date'] = drop_5['date']
        sample_data['drop_5_date'] = drop_5['date']
    
    # daily capacity, high, low, close among last 60 days
    base_index = df.index[df['date'] == the_date].to_list()[0]
    recent_60d = df.iloc[base_index - 60: base_index]
    # print(df.iloc[base_index - 60: base_index])
    # weekly capacity, high, low, close among last 52 weeks
    curr_week = df[df['date'] == the_date]['week'].iloc[0]
    week_prev_year = utils.week_prev_year(the_date)
    print(curr_week)
    recent_52w = df[(df['week'] < curr_week) & (df['week'] >= week_prev_year)]
    recent_52w = recent_52w[['week', 'close', 'transaction']].copy()
    print(recent_52w)
    gb_week = recent_52w.groupby(by=['week'], axis='columns').mean()
    print(gb_week)

    # monthly capacity, high, low, close amont last 36 months 
    plot(ofile_path, recent_60d, boundary)
    sys.exit(0)


def plot(ofile_path, recent_60d, boundary):
    dirname = os.path.basename(ofile_path)
    recent_60d.reset_index(drop=True, inplace=True)
    fig, ax = plt.subplots()
    ax.plot(recent_60d.index, recent_60d.close, color='red', marker='o')
    ax.set_ylim(boundary[1]['price'], boundary[0]['price'])
    ax.set_xlabel('Day')
    ax.set_ylabel('Price', color='red')
    ax2 = ax.twinx()
    ax2.plot(recent_60d.index, recent_60d.transaction, color='blue', marker='o')
    ax2.set_ylabel('Transaction', color='blue')
    ax2.set_ylim(boundary[1]['transaction'], boundary[0]['transaction'])
    fig.savefig(os.path.join(ofile_path, '%s.1.png' % dirname))
    

def gen_samples(df, id, output_folder):
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
            if not os.path.exists(ofile_path):
                print('sampling %s' % sample_date)
                sample(df, sample_date, ofile_path, boundary)
            else:
                print('%s has been sampled, skip.' % sample_date)
        sample_date = utils.nextday(sample_date)


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


def main():
    opt = parse_arg()
    gen_samples_for_stock('1216', opt)
    # print(stock_df)

    
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