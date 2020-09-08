#!/usr/bin/env bash

set -e

cat res/ascii
echo "                                 ... brought to you by Pyotek (https://pyotek.dev/donate)"
echo

if [[ $(whoami) == "pi" ]]; then
  echo "OK: Running as pi user."
else
  echo "Failure: Sorry, running with another user as 'pi' is not yet supported."
fi
sleep 5

echo "System information:"
lsb_release -a
sleep 1

echo "* Install system dependencies..."
sudo apt-get -qq update
# TODO(kdevo): Install smbus via pip instead (which one is the correct one?)
sudo apt-get -qq -y install raspi-config i2c-tools python3-venv python3-pip python3-smbus

echo "* Install and setup pipx..."
python3 -m pip -q install --user pipx
python3 -m pipx ensurepath

echo "* Install open-argon from source..."
#INSTALL_DIR="/opt/open-argon"
#export PIPX_BIN_DIR="${INSTALL_DIR}"
#sudo mkdir -p "${INSTALL_DIR}"
#sudo chown -R pi:pi "${INSTALL_DIR}"
python3 -m pipx install --system-site-packages -f -e .

echo "* Enable i2c using raspi-config (non-interactive)..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 0
# i2c needed for fan, gpio needed for button, video needed for temp
sudo usermod -aG i2c,gpio,video pi

echo "* Install systemd service 'argond' and poweroff script..."
sudo cp ./systemd/argond.service /etc/systemd/system/
#sudo systemctl enable argond
sudo cp ./systemd/argond-poweroff.sh /lib/systemd/system-shutdown/
sudo systemctl daemon-reload

echo "======================================================"
echo "! A reboot is required now. Please run 'sudo reboot' !"
echo "\      Pro Tip: Run 'argon doctor' afterwards        /"
echo " ==================================================== "
