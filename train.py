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


# ============================= #
# you can define your own model #
# ============================= #
# class myNet(nn.Module):
#     #define the layers
#     def __init__(self):
#         super(myNet, self).__init__()

#     def forward(self, x):
#         return x

class LeNet(nn.Module):
    #define the layers
    def __init__(self):
        super(LeNet, self).__init__()
        print('Building model...')
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 29 * 29, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)
        self.relu = nn.ReLU()
        
    # connect these layers
    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(-1, 16 * 29 * 29)
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x

class StockUp(object):
    """docstring for ChineseOCR"""
    def __init__(self, args):
        super(StockUp, self).__init__()

        self.args = args
        self.in_path = args.img_folder
        self.batch_size = 32
        self.lr = 0.001
        # question 1: 4% price up among coming month ? True or False
        # question 2: 5% price down among coming month? True or False
        self.classes = ['false', 'true']

        self.checkdevice()
        self.prepareData()
        self.getModel()
        if args.func == 'train':
            self.epoch = args.epoch
            self.train_acc = self.train()
            self.saveModel()
            self.showWeights()
        self.test()

    def checkdevice(self):
        # To determine if your system supports CUDA
        print("Check devices...")
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print("Current device:", self.device)

        # Also can print your current GPU id, and the number of GPUs you can use.
        print("Our selected device:", torch.cuda.current_device())
        print(torch.cuda.device_count(), "GPUs is available")
        return

    def prepareData(self):
        # The output of torchvision datasets are PILImage images of range [0, 1]
        # We transform them to Tensor type
        # And normalize the data
        # Be sure you do same normalization for your train and test data
        print('Preparing dataset...')

        # The transform function for train data
        # we keep the data source unchange, not decorate it. 
        transform_train = transforms.Compose([
            # transforms.RandomCrop(128, padding=4),
            # transforms.RandomHorizontalFlip(),
            # transforms.RandomRotation(30),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (1, 1, 1)),
            # you can apply more augment function
            # [document]: https://pytorch.org/docs/stable/torchvision/transforms.html
        ])

        # The transform function for test data
        transform_test = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (1, 1, 1)),
        ])


        self.trainset = torchvision.datasets.ImageFolder(self.in_path, transform=transform_train)
        self.testset = torchvision.datasets.ImageFolder(self.in_path, transform=transform_test)

        self.trainloader = torch.utils.data.DataLoader(self.trainset, batch_size=self.batch_size, shuffle=True)
        print('Size of train data: %d' % len(self.trainset))
        print('Size of train loader: %d' % len(self.trainloader))
        self.testloader = torch.utils.data.DataLoader(self.testset, batch_size=self.batch_size, shuffle=False)
        print('Size of test data: %d' % len(self.testset))
        print('Size of test loader: %d' % len(self.testloader))
        # you can also split validation set
        # self.validloader = torch.utils.data.DataLoader(self.validset, batch_size=self.batch_size, shuffle=True)
        return

    def getModel(self):
        # Build a Convolution Neural Network
        if self.args.func == 'train':
            self.net = LeNet()
            print(self.net)
            # Define loss function and optimizer
            self.criterion = nn.CrossEntropyLoss()
            self.optimizer = optim.SGD(self.net.parameters(), lr=self.lr, momentum=0.9)
        elif self.args.func == 'test':
            self.loadModel(self.args.model_path)
            self.criterion = nn.CrossEntropyLoss()
        return
        
    def train(self):
        print('Training model...')
        # Change all model tensor into cuda type
        # something like weight & bias are the tensor 
        self.net = self.net.to(self.device) 
        
        # Set the model in training mode
        # because some function like: dropout, batchnorm...etc, will have 
        # different behaviors in training/evaluation mode
        # [document]: https://pytorch.org/docs/stable/nn.html#torch.nn.Module.train
        self.net.train()
        for e in range(self.epoch):  # loop over the dataset multiple times
            running_loss = 0.0
            correct = 0
            for i, (inputs, labels) in enumerate(self.trainloader, 0):
                
                #change the type into cuda tensor 
                inputs = inputs.to(self.device) 
                labels = labels.to(self.device) 

                # zero the parameter gradients
                self.optimizer.zero_grad()

                # forward + backward + optimize
                outputs = self.net(inputs)
                # select the class with highest probability
                _, pred = outputs.max(1)
                # if the model predicts the same results as the true
                # label, then the correct counter will plus 1
                correct += pred.eq(labels).sum().item()
                
                loss = self.criterion(outputs, labels)
                
                loss.backward()
                self.optimizer.step()

                # print statistics
                running_loss += loss.item()
                if i % 100 == 99:    # print every 200 mini-batches
                    print('[%d, %5d] loss: %.3f' %
                          (e + 1, i + 1, running_loss / 100))
                    running_loss = 0.0

            print('%d epoch, training accuracy: %.4f' % (e+1, 100.*correct/len(self.trainset)))
        print('Finished Training')
        return 100.*correct/len(self.trainset)

    def test(self):
        print('==> Testing model..')
        # Change model to cuda tensor
        # or it will raise when images and labels are all cuda tensor type
        self.net = self.net.to(self.device)

        # Set the model in evaluation mode
        # [document]: https://pytorch.org/docs/stable/nn.html#torch.nn.Module.eval 
        self.net.eval()

        correct = 0
        running_loss = 0.0
        iter_count = 0
        class_correct = [0 for i in range(len(self.classes))]
        class_total = [0 for i in range(len(self.classes))]
        with torch.no_grad(): # no need to keep the gradient for backpropagation
            for data in self.testloader:
                images, labels = data
                images = images.to(self.device) 
                labels = labels.to(self.device)
                outputs = self.net(images)
                _, pred = outputs.max(1)
                correct += pred.eq(labels).sum().item()
                c_eachlabel = pred.eq(labels).squeeze()
                loss = self.criterion(outputs, labels)
                iter_count += 1
                running_loss += loss.item()
                for i in range(len(labels)):
                    cur_label = labels[i].item()
                    try:
                        class_correct[cur_label] += c_eachlabel[i].item()
                    except:
                        print(class_correct[cur_label])
                        print(c_eachlabel[i].item())
                    class_total[cur_label] += 1

        print('Total accuracy is: {:4f}% and loss is: {:3.3f}'.format(100 * correct/len(self.testset), running_loss/iter_count))
        print('For each class in dataset:')
        records = {}
        for i in range(len(self.classes)):
            print('Accruacy for {:18s}: {:4.2f}%'.format(self.classes[i], 100 * class_correct[i]/class_total[i]))
            records[self.classes[i]] = {'acc': 100 * class_correct[i]/class_total[i],
                                        'correct': class_correct[i],
                                        'total': class_total[i]}
        with open(os.path.join(self.args.output_path, 'records.json'), 'w') as ofile:
            ofile.write(json.dumps(records, indent=4))

    def saveModel(self):
        # After training , save the model first
        # You can saves only the model parameters or entire model
        # Some difference between the two is that entire model 
        # not only include parameters but also record hwo each 
        # layer is connected(forward method).
        # [document]: https://pytorch.org/docs/master/notes/serialization.html
        print('Saving model...')

        # only save model parameters
        torch.save(self.net.state_dict(), os.path.join(self.args.output_path, './weight.model.parameter.only.t7'))

        # you also can store some log information
        state = {
            'net': self.net.state_dict(),
            'acc': self.train_acc,
            'epoch': self.epoch
        }
        torch.save(state, os.path.join(self.args.output_path, './weight.t7'))

        # save entire model
        torch.save(self.net, os.path.join(self.args.output_path, './model.pt'))
        return

    def loadModel(self, path):
        print('Loading model...')
        if path.split('.')[-1] == 't7':
            # If you just save the model parameters, you
            # need to redefine the model architecture, and
            # load the parameters into your model
            self.net = LeNet()
            checkpoint = torch.load(path)
            self.net.load_state_dict(checkpoint['net'])
        elif path.split('.')[-1] == 'pt':
            # If you save the entire model
            self.net = torch.load(path)
        return

    def showWeights(self):
        w_conv1 = self.net.conv1.weight.cpu().detach().numpy().flatten()
        w_conv2 = self.net.conv2.weight.cpu().detach().numpy().flatten()
        w_fc1 = self.net.fc1.weight.cpu().detach().numpy().flatten()
        w_fc2 = self.net.fc2.weight.cpu().detach().numpy().flatten()
        w_fc3 = self.net.fc3.weight.cpu().detach().numpy().flatten()

        plt.figure(figsize=(24, 6))
        plt.subplot(1,5,1)
        plt.title("conv1 weight")
        plt.hist(w_conv1)

        plt.subplot(1,5,2)
        plt.title("conv2 weight")
        plt.hist(w_conv2)

        plt.subplot(1,5,3)
        plt.title("fc1 weight")
        plt.hist(w_fc1)

        plt.subplot(1,5,4)
        plt.title("fc2 weight")
        plt.hist(w_fc2)

        plt.subplot(1,5,5)
        plt.title("fc3 weight")
        plt.hist(w_fc3)

        plt.savefig(os.path.join(self.args.output_path, 'weights.png'))

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--img_folder', dest='img_folder', default='../dataset', help='The input image folder path.')
    parser.add_argument('--output_folder', dest='output_path', default='./', help='The model and result.')
    subparser = parser.add_subparsers(dest='func', help='Sub commands')
    train_args = subparser.add_parser('train', help='Train(then test) and output model.')
    train_args.add_argument('--epoch', dest='epoch', type=int, default=75, help='The number of epoch.')
    test_args = subparser.add_parser('test', help='Give input and test')
    test_args.add_argument('--model', dest='model_path', default='./model.pt', help='The path to saved model and results.')
    
    args = parser.parse_args()
    return args


def main():
    args = arg_parse()
    print(args.func)
    # you can adjust your hyperperamers
    # ocr = ChineseOCR('../dataset', 75, 32, 0.001)
    su = StockUp(args)


if __name__ == '__main__':
    main()
