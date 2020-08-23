import logging
from typing import Dict, Callable

import smbus
import RPi.GPIO as GPIO
import time


class IO:
    # IO Layout
    # ---------
    BUTTON_PIN = 4
    # You can also verify the address using `i2cdetect`:
    I2C_ADDR = 0x1a

    FAN_RPM = 11_000

    def __init__(self):
        # Setup IO
        self._bus = smbus.SMBus(1 if GPIO.RPI_REVISION in (2, 3) else 0)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def button_pushed(self, channel: int, callback=None):
        logging.info("Button pushed (channel: %s)", channel)
        if callback:
            callback()

    def set_power_mode(self, always_on=False):
        if always_on:
            logging.info("Set power mode to 'always on'")
            self._bus.write_byte_data(self.I2C_ADDR, 0, 0xFE)
        else:
            logging.info("Set powermode to default")
            self._bus.write_byte_data(self.I2C_ADDR, 0, 0xFD)

    def wait_for_button(self):
        while GPIO.input(self.BUTTON_PIN) == 0:
            pass

    def button_listen(self):
        start = time.time()
        while (time.time() - start) > 0.01:
            # if GPIO.input(self.BUTTON_PIN) == 1:
            #     print(push_count)
            #     push_count += 1
            #     start = time.time()
            print(GPIO.input(self.BUTTON_PIN), end=' ')

    def register_callback(self, callback):
        def callback_wrapper(_):
            """This weird debouncing circuit is needed because of the way the case sends the inputs to the Pi's GPIO"""
            logging.debug("Callback button debouncing started")
            signal_count = 1
            # Needed to differentiate between shutdown and multiple pushes:
            continuous = True
            falling = False
            start = time.time()
            while (time.time() - start) < 1.0:
                if GPIO.input(self.BUTTON_PIN) == 1:
                    signal_count += 1
                    start = time.time()
                    if falling:
                        continuous = False
                else:
                    falling = True
                time.sleep(0.01)

            if signal_count > 1:
                if continuous:
                    pushed_times = 1 if signal_count >= 4 else 2
                else:
                    pushed_times = signal_count - 1
                logging.info(f"Detected {signal_count}{' continuous' if continuous else ''} signals. "
                             f"Probably pushed {pushed_times} times.")
                if pushed_times == 1 and continuous:
                    callback('long')
                elif pushed_times == 2:
                    callback('double')
                else:
                    callback('many')
            else:
                logging.debug("Not a recognized button push")

        GPIO.add_event_detect(self.BUTTON_PIN, GPIO.RISING, callback=callback_wrapper)

    def set_fan_speed(self, speed_percent: int, i2c_addr=I2C_ADDR, debug=True):
        if 0 <= speed_percent <= 100:
            if debug:
                logging.debug("Set fan speed to %d%% (%d rpm)", speed_percent, self.guess_rpm(speed_percent))
            self._bus.write_byte_data(i2c_addr, 0, speed_percent)
        else:
            logging.error("Fan speed must be in range from 0 to 100.")

    def guess_rpm(self, speed):
        return round(speed / 100 * IO.FAN_RPM, 1)

    def notify_shutdown(self):
        # The following line has been extracted from argon1.sh:
        # As far as I understand, the 0xFF tells the case that a shutdown has been initiated.
        # From my logical standpoint, the following happens:
        # 1. OS: Software shutdown initiated
        # 2. OS: Tell Argon that system shuts down
        # 3. Argon: Wait until UART pin is V=0, because then the Pi shutdown is considered as completed
        # 4. Argon: Turn off the power internal supply (Red Power LED of the Pi turns off)
        # Ha! Guessed correctly! Found this afterwards: https://github.com/Argon40Tech/Argon-ONE-i2c-Codes/blob/master/README.md
        self.set_fan_speed(0)
        self._bus.write_byte_data(self.I2C_ADDR, 0, 0xFF)
