#!/home/user/anaconda3/bin/python
import torch
import torchvision
import torchvision.transforms as transforms
import torch.nn as nn
import torch.optim as optim
import os
import matplotlib.pyplot as plt
import numpy as np
import sys
import argparse
import json
from train import LeNet
from PIL import Image
import twstock
import pandas as pd
import codecs
from texttable import Texttable


def loadModel(group, model_root, device):
    print('Loading model...')
    up4_model_path = os.path.join(model_root, group, 'up4', 'model.pt')
    net_up4 = torch.load(up4_model_path)
    drop5_model_path = os.path.join(model_root, group, 'drop5', 'model.pt')
    net_drop5 = torch.load(drop5_model_path)
    net_up4 = net_up4.to(device)
    net_up4.eval()
    net_drop5 = net_drop5.to(device)
    net_drop5.eval()
    return net_up4, net_drop5


def checkdevice():
    # To determine if your system supports CUDA
    print("Check devices...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print("Current device:", device)

    # Also can print your current GPU id, and the number of GPUs you can use.
    print("Our selected device:", torch.cuda.current_device())
    print(torch.cuda.device_count(), "GPUs is available")
    return device


def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('group', help='The group of stock choose to predict.')
    parser.add_argument('datestr', help='The string of date to predict, eq. 2020_12_28')
    parser.add_argument('--model_root', dest='model_root', default='../model_root', help='The root folder of model.')
    parser.add_argument('--samples', dest='sample_folder', default='../samples', help='The root folder of stock info image.')  
    parser.add_argument('--output', dest='output_root', default='../predictions', help='The root folder of prediction output.')  
    args = parser.parse_args()
    return args


def prepare_imagefolder(group, datestr, sample_folder, output_root):
    # find all png of this group + date + predict_type, 
    # and create a new folder in output root, given only folder '1' 
    # link png into folder '1' (we don't need to care the answer
    stock_list = []
    # collect stock id list of group
    for key in twstock.codes.keys():
        if twstock.codes[key].group == group and\
                twstock.codes[key].market == '上市':
            stock_list.append(key)
    print('### %s ###' % group)
    pred_folder = os.path.join(output_root, '%s_%s' % (group, datestr))
    if not os.path.exists(pred_folder):
        os.mkdir(pred_folder)
    img_folder = os.path.join(pred_folder, 'img_folder')
    if not os.path.exists(img_folder):
        os.mkdir(img_folder)
    dest = os.path.join(img_folder, '1')
    if not os.path.exists(dest):
        os.mkdir(dest)
    if not os.path.exists(os.path.join(img_folder, '2')):    
        os.mkdir(os.path.join(img_folder, '2'))
    for idir in os.listdir(sample_folder):
        if idir.split('_')[0] not in stock_list: # not in this group
            continue
        date_postfix = '_'.join(idir.split('_')[1:])
        if date_postfix != datestr:
            continue
        dispatch_img(os.path.join(sample_folder, idir), dest)
    return img_folder


def dispatch_img(source_folder, dest_folder):
    dirname = os.path.basename(source_folder)
    png_path = os.path.join(source_folder, '%s.png' % dirname)
    png_path = os.path.abspath(png_path)
    # dest_path = os.path.join(dest_folder, '%s.png' % dirname)
    # print('dest path = %s' % dest_path)
    if not os.path.exists(png_path):
        return
    # print(png_path)
    dest_folder = os.path.abspath(dest_folder)
    create_link(png_path, dest_folder)


def create_link(real_path, linked_folder):
    dest = os.path.join(linked_folder, os.path.basename(real_path))
    if not os.path.exists(dest):
        print(real_path)
        os.symlink(real_path, dest)
        print('symbolic link %s created.' % dest)


def get_file_list(in_path):
    flist = []
    for f in os.listdir(os.path.join(in_path, '1')):
        if not f.endswith('.png'):
            continue
        flist.append(f)
    return flist


def prepare_data(group, datestr, sample_folder, output_root):
    # create one set of image folder is enough
    # no matter up4 or drop5, we use the same input. 
    in_path = prepare_imagefolder(group, datestr, sample_folder, output_root)
    output_folder = os.path.dirname(in_path)
    file_list = get_file_list(in_path)
    tranform_compose = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (1, 1, 1)),
    ])
    fullset = torchvision.datasets.ImageFolder(in_path, transform=tranform_compose)
    print('dataset size = %d' % len(fullset))
    # we have to keep trace the data and the mapping stock, or, 
    # we have to get them one by one. 
    the_loader = torch.utils.data.DataLoader(fullset, batch_size=len(fullset), shuffle=False)
    print('# batches = %d' % len(the_loader))
    return the_loader, file_list, output_folder


def detailize_result(r_up4, r_drop5, file_list, sample_root, output_folder):
    csv_lines = []
    csv_lines.append('id,name,date,up4,up4_trend,up4_false_raw,drop5,drop5_trend,drop5_false_raw,up4_predicted,drop5_predicted')
    for i in range(len(r_up4)):
        stock_id = file_list[i].split('_')[0]
        company_name = twstock.codes[stock_id].name
        date_str = file_list[i][len(stock_id) + 1:].replace('.png', '')
        # record id, name, date
        record = [stock_id, company_name, date_str]

        print('========= %s (%s) : %s ======' % (stock_id, company_name, date_str))
        w_up4_false = r_up4[i][0]
        w_up4_true = r_up4[i][1]
        up4 = w_up4_true.item() > w_up4_false.item()
        up4_score = (w_up4_true - w_up4_false, w_up4_false)
        # record up4,up4_trend,up4_false_raw
        record.append(str(int(up4)))
        record.append('%.1f' % up4_score[0])
        record.append('%.1f' % up4_score[1])

        w_drop5_false = r_drop5[i][0]
        w_drop5_true = r_drop5[i][1]
        drop5 = w_drop5_true.item() > w_drop5_false.item()
        drop5_score = (w_drop5_true - w_drop5_false, w_drop5_false)
        # record drop5,drop5_trend,drop5_false_raw
        record.append(str(int(drop5)))
        record.append('%.1f' % drop5_score[0])
        record.append('%.1f' % drop5_score[1])

        print('up4: %s (%.1f:%.1f) , ' % (up4, up4_score[0], up4_score[1]) +\
            'drop5: %s (%.1f:%.1f)' % (drop5, drop5_score[0], drop5_score[1]))
        gt_path = os.path.join(sample_root, file_list[i].replace('.png', ''), 'gt.json')
        if os.path.exists(gt_path):
            print('*** ground truth available ***')
            with open(gt_path, 'r') as jfile:
                gt = json.load(jfile)
                if gt['GT'][0] == int(up4):
                    print('up4 >>> predicted')
                    record.append('1')
                else:
                    print('up4 >>> missed')
                    record.append('-1')
                if gt['GT'][1] == int(drop5):
                    print('drop5 >> predicted')
                    record.append('1')
                else:
                    print('drop5 >>> missed')
                    record.append('-1')
            # record up4_predicted,drop5_predicted
        else:
            record.append('0')
            record.append('0')
        csv_lines.append(','.join(record))
    with codecs.open(os.path.join(output_folder, 'predictions.csv'), 'w', 'utf-8') as ofile:
        ofile.write('\n'.join(csv_lines))
    return os.path.join(output_folder, 'predictions.csv')
            

def predict(the_loader, models, device):
    m_up4, m_drop5 = models
    with torch.no_grad():
        for images, labels in the_loader: # only loop once
            # for images, lables in the_loader:
            images = images.to(device) 
            # print(images.shape)
            r_up4 = m_up4(images)
            r_drop5 = m_drop5(images)
            return r_up4, r_drop5
            

def summarize(summary_path):
    df = pd.read_csv(summary_path, header=0)
    up4_df = df[df['up4'] == 1].sort_values(['up4_trend'], ascending=False)
    up4_df_tb = up4_df[['id', 'name', 'up4_trend', 'drop5', 'up4_predicted']]
    up4_df_tb = up4_df_tb.rename(
        columns={
            'up4_trend': 'score',
            'drop5': 'predict drop5',
            'up4_predicted': 'hit/miss'})
    # up4_df_tb['score'] = up4_df['up4_trend']
    up4_df_tb['predict drop5'] = up4_df_tb['predict drop5'].apply(lambda x: 'yes' if x == 1 else 'no')
    up4_df_tb['hit/miss'] = up4_df_tb['hit/miss'].apply(lambda x: 'yet decided' if x == 0 else 'hit' if x == 1 else 'miss')
    # print(up4_df_tb)
    tb_up4 = Texttable()
    tb_up4.set_cols_align(['l', 'l', 'r', 'l', 'l'])
    tb_up4.set_cols_dtype(['t', 't', 'f', 't', 't'])
    # print(up4_df.columns.to_numpy().shape)
    tb_up4.header(up4_df_tb.columns.to_numpy())
    tb_up4.add_rows(up4_df_tb.values, header=False)
    print('##### predict up 4% in one month #####')
    print(tb_up4.draw())

    no_up4_df = df[df['up4'] == 0].sort_values(['up4_trend'], ascending=False)
    no_up4_df_tb = no_up4_df[['id', 'name', 'up4_trend', 'drop5', 'up4_predicted']]
    no_up4_df_tb = no_up4_df_tb.rename(
        columns={
            'up4_trend': 'score',
            'drop5': 'predict drop5',
            'up4_predicted': 'hit/miss'})
    # up4_df_tb['score'] = up4_df['up4_trend']
    no_up4_df_tb['predict drop5'] = no_up4_df_tb['predict drop5'].apply(lambda x: 'yes' if x == 1 else 'no')
    no_up4_df_tb['hit/miss'] = no_up4_df_tb['hit/miss'].apply(lambda x: 'yet decided' if x == 0 else 'hit' if x == 1 else 'miss')
    
    tb_no_up4 = Texttable()
    tb_no_up4.set_cols_align(['l', 'l', 'r', 'l', 'l'])
    tb_no_up4.set_cols_dtype(['t', 't', 'f', 't', 't'])
    # print(up4_df.columns.to_numpy().shape)
    tb_no_up4.header(no_up4_df_tb.columns.to_numpy())
    tb_no_up4.add_rows(no_up4_df_tb.values, header=False)
    print('##### predict NO up 4% in one month #####')
    print(tb_no_up4.draw())


def main():
    args = arg_parse()
    # classes = ['false', 'true']
    device = checkdevice()
    the_loader, file_list, output_folder = prepare_data(
        args.group, args.datestr, args.sample_folder, args.output_root)
    # print(file_list)  
    m_up4, m_drop5 = loadModel(args.group, args.model_root, device)
    r_up4, r_drop5 = predict(the_loader, (m_up4, m_drop5), device)
    summary_path = detailize_result(r_up4, r_drop5, file_list, args.sample_folder, output_folder)
    summarize(summary_path)
    # print(summary_path)


if __name__ == '__main__':
    main()