#!/bin/bash

cd src
nohup python3 bot_manager.py > ../nohup.out 2>&1 &
disown

sleep 1

export BOTPID=`ps aux | grep 'bot_manager.py' | grep -v grep | awk '{print($2)}'`
if [ -n "$BOTPID" ]; then
  echo "Running correctly."
else
  echo "ERROR: Script stopped."
  tail -n 10 ../nohup.out
fi
