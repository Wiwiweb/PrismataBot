#!/bin/bash

pkill -f bot_manager.py

cd /home/ec2-user/PrismataBot/src
nohup python3 bot_manager.py > /home/ec2-user/PrismataBot/nohup.out 2>&1 &
disown
