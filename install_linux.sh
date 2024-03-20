#!/bin/bash

echo -e "\e[1;32m Installing Apt Dependencies... \e[0m"
sudo apt install usbmuxd python3-tk
echo -e "\e[1;32m Installing PyBindGen... \e[0m"
pip3 install pybindgen
echo -e "\e[1;32m Installing Dependencies... \e[0m"
pip3 install -r requirments.txt
echo -e "\e[1;32m Installing PyAFF4... \e[0m"
cd pyaff4 || { echo -e "\e[1;31m Could not find PyAFF4. Clone Afflux with '--recursive'. \e[0m"; exit; }
python3 setup.py install
echo -e "\e[1;32m Installing PyMobileDevice3... \e[0m"
cd ../pymobiledevice3 || { echo -e "\e[1;31m Could not find PyAFF4. Clone Afflux with '--recursive'. \e[0m"; exit; }
python3 setup.py install
echo -e "\e[1;32m Done. \e[0m"