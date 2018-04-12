#!/bin/bash

export BOTPID=`ps aux | grep 'bot_manager.py' | grep -v grep | awk '{print($2)}'`
if [ -n "$BOTPID" ]; then
  echo "Running correctly."
else
  echo "ERROR: Script stopped."
  tail -n 10 /home/ec2-user/nohup.out
  exit 1
fi
