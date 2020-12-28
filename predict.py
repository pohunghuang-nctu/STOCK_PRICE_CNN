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
from PIL imporg Image


def loadModel(path):
    print('Loading model...')
    if path.split('.')[-1] == 't7':
        # If you just save the model parameters, you
        # need to redefine the model architecture, and
        # load the parameters into your model
        net = LeNet()
        checkpoint = torch.load(path)
        net.load_state_dict(checkpoint['net'])
    elif path.split('.')[-1] == 'pt':
        # If you save the entire model
        net = torch.load(path)
    return net


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
    parser.add_argument('datestr', help='The string of date to predict, eq. 2020_12_28')
    parser.add_argument('--model_root', dest='model_root', default='../model_root', help='The root folder of model.')
    parser.add_argument('--img_root', dest='img_root', default='../img_root', help='The root folder of stock info image.')  
    parser.add_argument('--output', dest='output', default='../predictions', help='The root folder of prediction output.')  
    args = parser.parse_args()
    return args


def prepare_imagefolder(group, datastr, predict_type, img_root, output_root):
    # find all png of this group + date + predict_type, 
    # and create a new folder in output root, given only folder '1' 
    # link png into folder '1' (we don't need to care the answer
    pass

def prepare_data(group, datestr, img_root):
    # create one set of image folder is enough
    # no matter up4 or drop5, we use the same input. 
    in_path = prepare_imagefolder(group, datestr, img_root)
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
    args = arg_parse()
    classes = ['false', 'true']
    m_up4, m_drop5 = loadModel(args.group, args.model_root)
    device = checkdevice()
    m_up4 = m_up4.to(device)
    m_up4.eval()
    m_drop5 = m_up4.to(device)
    m_drop5.eval()
    the_loader = prepare_data(args.group, args.datestr, args.img_root)
    the_result = predict(the_loader, (m_up4, m_drop5))


if __name__ == '__main__':
    main()