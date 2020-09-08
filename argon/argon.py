import configparser as ini
import logging
import os
import subprocess
import signal
import time
import distutils.util
from pathlib import Path
from random import randint

import click
import click.termui

import argon.util as util
from argon.ctrl import IO


class Argon:
    DAEMON_NAME = 'argond'
    SYSTEMCTL_PATH = '/etc/systemd/system'
    SYSTEMCTL_SHUTDOWN_DROPIN = '/lib/systemd/system-shutdown'

    def __init__(self, config_file='config.ini', verbose=True):
        self._config_file = Path(config_file)
        self._verbose = verbose

        logging.debug("Initializing IO: i2c (for controlling fan) and GPIO (for button)")
        self._io = IO()

        self._cfg = ini.ConfigParser()
        if self._config_file.exists():
            self._cfg.read(self._config_file)
        else:
            self._cfg['Settings'] = {
                'fan_profile': 'Fan:Vendor',
                'temp_check_interval': 10,
                'button_profile': 'Button:Vendor',
                'power_mode_always_on': False,
            }
            self._cfg['Fan:Vendor'] = {'55': '10', '60': '55', '65': '100'}
            self._cfg['Fan:Silent'] = {'60': '80', '65': '100'}
            self._cfg['Fan:Speedy'] = {'45': '10', '50': '40', '55': '100'}
            self._cfg['Fan:Off'] = {'0': '0'}
            self._cfg['Fan:On'] = {'0': '100'}

            self._cfg['Button:Vendor'] = {'long': 'sudo shutdown -h now',
                                          'double': 'sudo reboot',
                                          'many': ''}
            self._cfg['Button:Better'] = {'long': 'sudo shutdown -h now',
                                          'double': 'sudo shutdown -h now',
                                          'many': 'sudo reboot'}
            with self._config_file.open('w') as file:
                self._cfg.write(file)

    def banner(self, name=None) -> tuple:
        if not name:
            banners = os.listdir('res')
            name = banners[randint(0, len(banners) - 1)]
        with open(f'res/{name}') as banner:
            height = 0
            width = 0
            for line in banner:
                click.secho(line, nl=False)
                width = max(width, len(click.termui.strip_ansi(line)))
                height += 1
        return width, height

    def service_status(self):
        return subprocess.run(f'systemctl status {self.DAEMON_NAME} > /dev/null', shell=True).returncode

    def start_service(self):
        logging.info(f"Start {self.DAEMON_NAME} service")
        subprocess.run(f'sudo systemctl start {self.DAEMON_NAME}', shell=True).check_returncode()

    def stop_service(self):
        logging.info(f"Stop {self.DAEMON_NAME} service")
        subprocess.run(f'sudo systemctl stop {self.DAEMON_NAME}', shell=True).check_returncode()

    def enable_service(self):
        logging.info(f"Enable {self.DAEMON_NAME} service")
        subprocess.run(f'sudo systemctl enable {self.DAEMON_NAME}', shell=True).check_returncode()

    def doctor(self, hw_check=True, sw_check=True):
        self.banner('banner' if click.get_terminal_size()[0] > 124 else 'banner-small')

        util.info("Welcome! This utility will check if your Argon One case is working as expected.")

        errors = 0
        if self.service_status() == 0:
            if click.confirm("Daemon 'argond' already running via systemd. "
                             "This will interfere with the hardware checks. Stop daemon?"):
                self.stop_service()
            else:
                util.warning("You have been warned. Cancel anytime via 'CTRL+C'.")

        click.echo()
        if hw_check:
            util.info("Let's check the hardware first.")
            click.secho("Push the button on your Argon case twice (fast). ", bold=True, nl=False)
            click.echo(click.style("Waiting for you ..."))
            self._io.wait_for_button()
            if click.confirm("Did you just push the button?"):
                util.success("Nice, the button works fine.")
            else:
                util.error("Something strange happened - if it wasn't you, I received a ghost touch.")
                click.echo("This can have multiple causes: "
                           "Additional hardware attached that interferes with the case, wrong assembly etc.")
                click.echo("In the latter case, compare your assembly with "
                           "https://github.com/pyotek/open-argon#overview")
                errors += 1

            click.echo()
            click.echo("Next, we are going to test the fan.")
            click.pause()
            with click.progressbar(range(0, 105, 5),
                                   fill_char='█', empty_char=' ', show_eta=False, show_percent=False,
                                   item_show_func=lambda s: f"{self._io.guess_rpm(s)} rpm"
                                   if s else 'N/A rpm') as bar:
                for p in bar:
                    self._io.set_fan_speed(p, debug=False)
                    time.sleep(0.5)
            time.sleep(1.0)
            self._io.set_fan_speed(0, debug=False)
            if click.confirm("Did you hear the fan's varying sound?"):
                util.success("Cool, this will keep your Pi ice-cold... Well - nearly!")
            else:
                util.error("Check the fan wiring!")
                click.echo("Tip: Compare assembly with image at https://github.com/pyotek/open-argon#fan")
                errors += 1
            click.echo()

        if sw_check:
            util.info("Let's check the software side now!")
            try:
                temp = util.get_temp()
                util.success(f"Current temperature: {temp}")
            except:
                logging.exception("Unable to get temperature via 'vcgencmd' tool")
                util.error("Could not get the temperature.")
                # TODO(kdevo): Automatize adding user to video group
                click.echo("Tip: Ensure that the current user belongs to the 'video' group!")
                errors += 1

            if Path(self.SYSTEMCTL_PATH).joinpath(f'{self.DAEMON_NAME}').exists() \
                    and Path(self.SYSTEMCTL_SHUTDOWN_DROPIN).joinpath(f'{self.DAEMON_NAME}-poweroff.sh').exists():
                util.error("Some necessary files for the daemon are missing. Consider to re-run the installer!")
                errors += 1

            status = self.service_status()
            if status == 0:
                util.success("Open Argon daemon 'argond' is running.")
            else:
                click.echo("Open Argon daemon 'argond' is NOT running!")
                if click.confirm("Enable and start it now via systemd?"):
                    self.enable_service()
                    self.start_service()
                else:
                    util.error("Not running the daemon does not allow you to fully enjoy the case.")
                    errors += 1

        click.echo("=" * click.termui.get_terminal_size()[0])
        if errors == 0:
            util.success("Great, passed all checks! Have fun with your case!")
        else:
            util.error(f"There is a total of {errors} error(s). Carefully read the error messages above for advice.")

    def set_fan(self, speed):
        self._io.set_fan_speed(speed)

    def handle_button(self, button_profile, interaction_type):
        action = self._cfg[button_profile][interaction_type]
        logging.info(f"Action '{action}' has been triggered by button ('{interaction_type}' interaction).")
        subprocess.Popen(action, shell=True)

    def daemon(self, fan_profile=None, button_profile=None):
        self._io.set_power_mode(distutils.util.strtobool(self._cfg['Settings']['power_mode_always_on']))
        running = True
        if self.service_status() == 0:
            logging.warning("Another 'argond' daemon is already running via systemd. "
                            "Running two instances simultaneously is only recommended for testing purposes.")

        def status_signal_received(signum, frame):
            logging.warning(f"SIGUSR1 #{signum} received. Sending status.")
            # TODO(kdevo)


        def shutdown_signal_received(signum, frame):
            logging.warning(f"SIGUSR2 #{signum} received. Preparing for shutdown.")
            nonlocal running
            running = False
            self._io.notify_shutdown()

        # TODO(kdevo): A future shutdown can also be signaled with SIGUSR2 (e.g. `systemctl kill -s SIGUSR1 argond`),
        #   but because usually the systemd shutdown script is installed, this does not have any effect.
        signal.signal(signal.SIGUSR2, shutdown_signal_received)
        signal.signal(signal.SIGUSR1, status_signal_received)
        if os.getuid() != 0:
            logging.warning("Daemon not started as root. Will probably not be able to shutdown.")
        if not fan_profile:
            fan_profile = self._cfg['Settings']['fan_profile']
        if not button_profile:
            button_profile = self._cfg['Settings']['button_profile']
        logging.info("Running in daemon/driver mode.")
        logging.debug(f"Button profile: {button_profile}")
        self._io.register_callback(lambda t: self.handle_button(button_profile, t))

        logging.info(f"Fan profile: {fan_profile}")
        check_interval = float(self._cfg['Settings']['temp_check_interval'])
        # Sorting descending ensures that...
        #   a) items have the an order
        #   b) the correct fan speed is set immediately instead of step-wise
        temps = sorted([int(t) for t in self._cfg[fan_profile]], reverse=True)
        # TODO(kdevo): Refactor to separate fan class:
        speed = None
        logging.debug(f"Sorted temperatures of the profile: {temps}")

        # TODO(kdevo): Useful for possible tests:
        # def fake_temp():
        #     return randint(40, 100)
        # util.get_temp = fake_temp

        while running:
            cur_temp = util.get_temp()
            logging.debug(f"Got current temperature: {cur_temp}°C")
            for target_temp in temps:
                if cur_temp >= target_temp:
                    new_speed = int(self._cfg[fan_profile][str(target_temp)])
                    if speed == new_speed:
                        logging.debug(f"Fan already running at specified speed {new_speed}%, no need to set it again.")
                        break
                    logging.info(f"Set fan speed to {new_speed}%. "
                                 f"Target temperature exceeded: {cur_temp}°C >= {target_temp}°C")
                    self._io.set_fan_speed(new_speed)
                    speed = new_speed
                    break
            else:
                if speed > 0:
                    logging.info("No given temperature has been exceeded. Turning off fan.")
                    self.set_fan(0)
                    speed = 0

            logging.debug(f"Sleeping {check_interval} seconds...")
            time.sleep(check_interval)

    # TODO
    # def status(self):
    #     click.echo()
    #     click.echo("Active fan profile: {} running at {} (temperature: )")
    #     click.echo("Active button profile: {}")
    #     systemd/daemon status etc.

    def notify_shutdown(self):
        logging.info("Got notification for final shutdown sequence (usually called by systemd).")
        self._io.notify_shutdown()
        logging.info("Final shutdown sequence finished, told Argon to shutdown case circuit.")

    def configure(self):
        logging.info(f"Opening configuration file '{self._config_file}' with preferred text editor.")
        old_cfg = self._config_file.read_text()
        click.edit(filename=self._config_file, extension='.ini')
        new_cfg = self._config_file.read_text()
        if old_cfg == new_cfg:
            logging.info("No changes have been made.")
        else:
            logging.info("Detected changes.")
            if click.confirm("Apply the changes you just made? This will restart the argon service."):
                util.info("Restarting via systemctl.")
                subprocess.run('sudo systemctl restart argond', shell=True)
            else:
                util.info("Changes will not be applied.")
