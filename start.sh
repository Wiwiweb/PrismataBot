#!/bin/bash

# Kill if started
export BOTPID=`ps aux | grep 'main.py' | grep -v grep | awk '{print($2)}'`
if [ -n "$BOTPID" ]; then
  echo "Killing old process "$BOTPID"."
  kill $BOTPID
fi

# Update from git
echo "Pulling latest git version"
git pull

# Start
echo "Starting"
nohup python3 main.py > nohup.out 2>&1 &
disown

sleep 1

export BOTPID=`ps aux | grep 'main.py' | grep -v grep | awk '{print($2)}'`
if [ -n "$BOTPID" ]; then
  echo "Running correctly."
else
  echo "ERROR: Script stopped."
fi
