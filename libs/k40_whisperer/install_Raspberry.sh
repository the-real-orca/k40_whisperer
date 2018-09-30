#!/bin/sh
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# prepare system 
sudo groupadd lasercutter
sudo usermod -a -G lasercutter pi
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="5512", ENV{DEVTYPE}=="usb_device", MODE="0664", GROUP="lasercutter"' | sudo tee /etc/udev/rules.d/97-ctc-lasercutter.rules > /dev/null

# get dependencies
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install python3 python3-pip git -y
sudo apt-get install inkscape libjpeg-dev zlib1g-dev -y 
sudo pip3 install --upgrade pip 

# install K40 Whisperer
cd ~
git clone https://github.com/the-real-orca/k40_whisperer.git
cd k40_whisperer
sudo pip3 install -r requirements.txt
sudo chmod a+x k40_whisperer.py

# run at startup
sudo apt-get install supervisor
sudo cp -f laser_whisperer_script.conf /etc/supervisor/conf.d/
sudo service supervisor restart


# finished
echo
echo "  ${RED}connect the K40 USB${NC} and ${RED}restart Rasperry Pi${NC}"
echo "  ${GREEN}YOU ARE READY TO CUT!${NC}"
echo


