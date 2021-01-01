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
import cv2


def loadModel(group, model_root):
    print('Loading model...')
    up4_model_path = os.path.join(model_root, group, 'up4', 'model.pt')
    net_up4 = torch.load(up4_model_path)
    drop5_model_path = os.path.join(model_root, group, 'drop5', 'model.pt')
    net_drop5 = torch.load(drop5_model_path)
    return net_up4, net_drop5


def predict(img_path, net, transforms):
    ## ToDo #####
    with open(path, 'rb') as f:
        img = Image.open(f)
        return img.convert('RGB')
    for trans in transforms:
        img = trans.forward(img)
    images = [img].to(self.device)
    output = self.net(images)[0] 
    


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
    parser.add_argument('img_path', help='img path.')
    # parser.add_argument('datestr', help='The string of date to predict, eq. 2020_12_28')
    parser.add_argument('--model_root', dest='model_root', default='../model_root', help='The root folder of model.')
    
    # parser.add_argument('--samples', dest='sample_folder', default='../samples', help='The root folder of stock info image.')  
    # parser.add_argument('--output', dest='output_root', default='../predictions', help='The root folder of prediction output.')  
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
    if not os.path.exists(png_path):
        return
    create_link(png_path, dest_folder)


def create_link(real_path, linked_folder):
    dest = os.path.join(linked_folder, os.path.basename(real_path))
    if not os.path.exists(dest):
        os.symlink(real_path, dest)
        print('symbolic link %s created.' % dest)


def prepare_data(group, datestr, sample_folder, output_root):
    # create one set of image folder is enough
    # no matter up4 or drop5, we use the same input. 
    in_path = prepare_imagefolder(group, datestr, sample_folder, output_root)
    tranform_compose = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (1, 1, 1)),
    ])
    fullset = torchvision.datasets.ImageFolder(in_path, transform=tranform_compose)
    # we have to keep trace the data and the mapping stock, or, 
    # we have to get them one by one. 
    the_loader = torch.utils.data.DataLoader(fullset, batch_size=len(fullset), shuffle=False)
    return the_loader


def main():
    device = checkdevice()
    args = arg_parse()
    m_up4, m_drop5 = loadModel(args.group, args.model_root)
    m_up4 = m_up4.to(device)
    m_up4.eval()
    m_drop5 = m_drop5.to(device)
    m_drop5.eval()
    # img = cv2.imread(args.img_path)
    # img = img.convert('RGB')
    tranform_compose = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (1, 1, 1)),
    ])
    dataset = torchvision.datasets.ImageFolder(args.img_path, transform=tranform_compose)
    print('Size of data: %d' % len(dataset))
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=len(dataset), shuffle=False)
    print('batches of loader: %d' % len(dataloader))
    with torch.no_grad():
        for images, lables in dataloader:
            images = images.to(device) 
            print(images.shape)
            r_up4 = m_up4(images)
            r_drop5 = m_drop5(images)
            #print(p_up4.shape)
            _, p_up4 = r_up4.max(1)
            _, p_drop5 = r_drop5.max(1)
            print(p_up4)
            print(p_drop5)
    sys.exit(0)
    # img = tranform_compose(img)
    # img = img.to(device)
    # print(img.shape)
    # images = np.array([img])
    print(images.shape)
    sys.exit(0)
    output = m_up4(img)  
    dir(output)   
    sys.exit(0)
    
    classes = ['false', 'true']
    the_loader = prepare_data(
        args.group, args.datestr, args.sample_folder, args.output_root)  
    sys.exit(0)  
    
    
    m_up4 = m_up4.to(device)
    m_up4.eval()
    m_drop5 = m_up4.to(device)
    m_drop5.eval()
    the_result = predict(the_loader, (m_up4, m_drop5))


if __name__ == '__main__':
    main()