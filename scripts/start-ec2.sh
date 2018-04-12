#!/bin/bash

cd /home/ec2-user/PrismataBot/src
nohup python3 bot_manager.py > ../nohup.out 2>&1 &
disown
