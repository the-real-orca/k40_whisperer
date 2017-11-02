 Raspberry Pi with LCD Touchscreen
====================================

Automatic Installation
----------------------

```bash
wget https://raw.githubusercontent.com/the-real-orca/k40_whisperer/master/install_Raspberry.sh
chmod a+x ./install_Raspberry.sh
./install_Raspberry.sh
```

Manual Installation
-------------------

###System

```bash
sudo raspi-config -> enable SSH
sudo apt-get update
sudo apt-get upgrade -y
```


###Install K40-Whisperer

**unplug K40**

```bash
sudo groupadd lasercutter
sudo usermod -a -G lasercutter pi
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="5512", ENV{DEVTYPE}=="usb_device", MODE="0664", GROUP="lasercutter"' | sudo tee /etc/udev/rules.d/97-ctc-lasercutter.rules


git clone https://github.com/the-real-orca/k40_whisperer.git
cd k40_whisperer
sudo apt-get install python-pip
sudo apt-get install inkscape libjpeg-dev zlib1g-dev -y
sudo pip install --upgrade pip 
sudo pip install -r requirements.txt
```

**replug K40, restart Raspberry Pi**

`python k40_whisperer.py`


### 5" Display (XPT2046 driver)

https://www.raspberrypi.org/forums/viewtopic.php?t=143581

*/boot/config.txt*
```
dtparam=i2c_arm=on
dtparam=spi=on
dtoverlay=ads7846,penirq=25,speed=10000,penirq_pull=2,xohms=150
```
*/etc/X11/xorg.conf.d/99-calibration.conf*
```
Section "InputClass"
        Identifier "calibration"
        MatchProduct "ADS7846 Touchscreen"
        Option "Calibration" "3853 170 288 3796"
        Option "SwapAxes" "1"
EndSection
```

### 3.5" Display

https://www.elecrow.com/wiki/index.php?title=3.5_Inch_480x320_TFT_Display_with_Touch_Screen_for_Raspberry_Pi

```bash
git clone https://github.com/Elecrow-keen/Elecrow-LCD35.git
cd Elecrow-LCD35
sudo ./Elecrow-LCD35
```


###Install Pi-Whisperer

```bash
cd k40_whisperer
sudo pip install flask-socketio
```


