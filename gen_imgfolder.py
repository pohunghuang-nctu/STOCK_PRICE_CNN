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


all_group_list = []
for key in twstock.codes:
    if twstock.codes[key].group not in all_group_list:
        all_group_list.append(twstock.codes[key].group)


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--groups', nargs='+', type=str, default=['食品工業'], help='the groups of stock:' + ','.join(all_group_list))
    parser.add_argument('--imgroot', type=str, default=os.getcwd(), help='the root of image folders')
    parser.add_argument('--samples', type=str, default=os.path.join(os.getcwd(), 'samples'), help='the folder path of generated samples')
    opt = parser.parse_args()
    return opt


def dispatch_img(source_folder, group_folder):
    with open(os.path.join(source_folder, 'gt.json'), 'r') as jfile:
        gt = json.load(jfile)
    sample_date = os.path.basename(source_folder)
    png_path = os.path.join(source_folder, '%s.png' % sample_date)
    if not os.path.exists(png_path):
        return
    if gt['GT'][0] == 1: # up4 == True
        create_link(png_path, os.path.join(group_folder, 'up4', '2'))
    else:
        create_link(png_path, os.path.join(group_folder, 'up4', '1'))
    if gt['GT'][1] == 1: # drop5 == True
        create_link(png_path, os.path.join(group_folder, 'drop5', '2'))
    else:
        create_link(png_path, os.path.join(group_folder, 'drop5', '1'))


def create_link(real_path, linked_folder):
    dest = os.path.join(linked_folder, os.path.basename(real_path))
    if not os.path.exists(dest):
        os.symlink(real_path, dest)
        print('symbolic link %s created.' % dest)


def imgfolder_for_group(group, stock_list, opt):
    img_root = opt.imgroot
    group_folder = os.path.join(img_root, group)
    if not os.path.exists(group_folder):
        os.mkdir(group_folder)
        os.mkdir(os.path.join(group_folder, 'up4'))
        os.mkdir(os.path.join(group_folder, 'up4', '1'))
        os.mkdir(os.path.join(group_folder, 'up4', '2'))
        os.mkdir(os.path.join(group_folder, 'drop5'))
        os.mkdir(os.path.join(group_folder, 'drop5', '1'))
        os.mkdir(os.path.join(group_folder, 'drop5', '2'))
    sample_folder = opt.samples
    for s_dir in os.listdir(sample_folder):
        if not os.path.isdir(os.path.join(sample_folder, s_dir)):
            continue
        if not os.path.exists(os.path.join(sample_folder, s_dir, 'gt.json')):
            # yet ground truth
            continue
        if s_dir.split('_')[0] not in stock_list:
            continue
        dispatch_img(os.path.join(sample_folder, s_dir), group_folder)


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
        imgfolder_for_group(group, stock_list, opt)
    

if __name__ == '__main__':
    main()