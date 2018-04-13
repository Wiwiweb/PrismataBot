#!/bin/bash

export BOTPID=`ps aux | grep 'bot_manager.py' | grep -v grep | awk '{print($2)}'`
if [ -n "$BOTPID" ]; then
  echo "Running correctly."
else
  echo "ERROR: Script stopped."
  echo "=== Nohup: ==="
  tail -n 25 /home/ec2-user/PrismataBot/nohup.out
  echo "=== Bot log: ==="
  tail -n 25 /home/ec2-user/PrismataBot/logs/prismatabot.log
  exit 1
fi
