#!/usr/bin/env bash

set -e

cat res/ascii
echo "                                 ... brought to you by Pyotek (https://pyotek.dev/donate)"
sleep 5

echo "System information:"
lsb_release -a
sleep 1

echo "* Install system dependencies..."
sudo apt update
#sudo apt upgrade
# TODO(kdevo): Install smbus via pip instead (which one is the correct one? Pimoroni seems to maintain 'smbus')
sudo apt install raspi-config i2c-tools python3-venv python3-pip python3-smbus

echo "* Install and setup pipx..."
python3 -m pip install --user pipx
python3 -m pipx ensurepath
echo "* Install open-argon from source..."
python3 -m pipx install --system-site-packages -f -e .

echo "* Enable i2c using raspi-config (non-interactive)..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 0

echo "* Enable systemd service 'argond' and poweroff script..."
sudo cp ./systemd/argond.service /etc/systemd/system/
#sudo systemctl enable argond
sudo cp ./systemd/argond-poweroff.sh /lib/systemd/system-shutdown/

echo "======================================================"
echo "! A reboot is required now. Please run 'sudo reboot' !"
echo "\      Pro Tip: Run 'argon doctor' afterwards        /"
echo " ===================================================="
