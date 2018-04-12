#!/bin/bash

# Kill if started
export BOTPID=`ps aux | grep 'bot_manager.py' | grep -v grep | awk '{print($2)}'`
if [ -n "$BOTPID" ]; then
  echo "Killing old process "$BOTPID"."
  kill $BOTPID
fi

# Update from git
echo "Pulling latest git version"
git pull

# Start
echo "Starting"
cd ../src
nohup python3 bot_manager.py > ../nohup.out 2>&1 &
disown

sleep 1

export BOTPID=`ps aux | grep 'bot_manager.py' | grep -v grep | awk '{print($2)}'`
if [ -n "$BOTPID" ]; then
  echo "Running correctly."
else
  echo "ERROR: Script stopped."
  echo "=== Nohup: ==="
  tail -n 10 /home/ec2-user/PrismataBot/nohup.out
  echo "=== Bot log: ==="
  tail -n 10 /home/ec2-user/PrismataBot/logs/prismatabot.log
  exit 1
fi