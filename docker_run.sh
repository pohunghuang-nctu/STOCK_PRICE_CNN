#!/bin/bash
docker run -it -v /home/user/final_proj/data_host:/data_container --gpus all --name container_final pytorch/pytorch:lab2 bash
