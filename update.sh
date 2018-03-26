#!/bin/sh
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# clone branch
#git clone -b laser_whisperer https://github.com/the-real-orca/k40_whisperer.git laser_whisperer

# update Laser Whisperer
git pull
sudo pip install -r requirements.txt
sudo chmod a+x laser_whisperer.py

