#!/usr/bin/env bash

# Documentation of this mechanism: https://www.freedesktop.org/software/systemd/man/systemd-halt.service.html
if [[ "$1" == "halt" || "$1" == "poweroff" ]]; then
  #sudo systemctl -s SIGUSR1 argond
  /home/pi/.local/bin/argon _notify-shutdown
fi
