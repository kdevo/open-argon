Pyotek presents...

<img src="https://github.com/pyotek/open-argon/raw/master/.github/open-argon.gif" alt="Open Argon Logo" width="400" height="400">

> Argon is a chemical element with the symbol Ar and atomic number 18. It is in group 18 of the periodic table and is a noble gas. Argon is the third-most abundant gas in the Earth's atmosphere, at 0.934%. Source: [Wikipedia](https://en.wikipedia.org/wiki/Argon)

Okay. 

---

No, really - this repository is about providing an alternative code base for your **Argon One** Raspberry Pi case.
Read about the origin story and motivation behind this project [here](https://pyotek.dev/p/open-argon/)!

> :warning: This project is in an early stage. Beta testers wanted! Feel free to open an issue if you encounter a bug.

## Features

- Fancy CLI made with `click`
- Simple [configuration](#configuration) via INI-file:
    - Fan profiles to configure the temperature curve
    - Button profiles to configure button events and their actions
- Let the [`doctor`](#doctor) command check for working hard- and software
- Configurable power mode
- No root privileges needed for simple commands via `pipx`
- Simple installation routine from source
- Maintainable code base with Open Source community potential

Plus all the features of the proprietary [argon1.sh](https://download.argon40.com/argon1.sh) script.

## Quick Start

Installing from source is simple and recommended, as it also brings the advantage of using git transparently for further upgrades.

Invoke the following commands the `pi` user (`root` is **not** supported):

```shell script
cd ~
git clone https://github.com/pyotek/open-argon.git
cd open-argon
less install.sh # OPTIONAL: It's recommended to check the source before executing anything
./install.sh
```

After a `sudo reboot`, it is a good time to test everything: Try the [`argon doctor`](#doctor) command.

Then, [configure](#settings) with `argon config`.
Get more commands and help with `argon --help`.

> All of these commands work with normal user privileges, no need to be root (tested on the latest Pi OS), only the daemon which is controlled via systemd usually needs superuser privileges.

## Configuration

The default settings are the vendor's settings for legacy purposes, see also: [Waveshare Wiki](https://www.waveshare.com/wiki/PI4-CASE-ARGON-ONE).

Configuring them is just an `argon config` call away!

### Fan Settings

| CPU Temp | Fan Speed |
| :------: | :-------: |
| 55°C     | 10%       |
| 60°C     | 55%       |
| 65°C     | 100%      |

Configurable with a simple mapping within a `Fan:Profile` section, e.g. `55 = 10` represents the first row of the table.

`Fan:Vendor` is the default `fan_profile` setting, but the `Fan:Silent` is recommended as it reacts fast enough to cool while still keeping your case silent enough.

### Button Settings

The stock configuration from the producer is as follows:

| Button Input | Function        | Software Control
| :----------: | :-------------: | ----------------
| Hold < 3s    | None            | ✗ (filtered by MCU)
| Hold >=3s    | Safe Shutdown   | ? 
| Hold >=5s    | Hard Shutdown   | ✗ (triggered by MCU)
| Push 2x      | Reboot          | ✓

Holding less than 3s does not trigger anything. This is (seemingly) filtered on the hardware side the MCU on the case's mainboard itself.

The above above configuration is not chosen very well, 
because 2 seconds difference between a safe and a hard shutdown is not really safe.

> :warning: Additionally, there is [an open issue](https://github.com/pyotek/open-argon/issues/1) which still needs to be investigated!

For the above reason, we provide the following `Button:Better` profile:

| Button Input | Keyword         | Action 
| :----------: | :-------------: | ----------------
| Hold >=3s    | `long`          | `sudo shutdown -h now`
| Push 2x      | `double`        | `sudo shutdown -h now`
| Push >= 4x   | `many`          | `sudo reboot`

Note that Open Argon has the ability to detect more than 4 subsequent pushes (`many`) in contrary to the official script.
This way, you do not rely on the 3s `long` timing. Relying on simple counting is probably safer than counting seconds with your inner clock - and you probably do not want to get your stopwatch out, either.

## Doctor

Test your assembly by running `argon doctor`.

The following images might help to see if there is something wrong on the hardware side (they all link to waveshare.com):

### Hardware Overview

![Quick Assembly](https://www.waveshare.com/img/devkit/accessories/PI4-CASE-ARGON-ONE/PI4-CASE-ARGON-ONE-13_800.jpg)

#### Fan

![Fan Assembly](https://www.waveshare.com/img/devkit/accessories/PI4-CASE-ARGON-ONE/PI4-CASE-ARGON-ONE-9_800.jpg)

## Mods 

### Fan Upgrade

[Martin Rowan](https://www.martinrowan.co.uk/2019/12/argon-one-pi-4#noise) exchanged the fan to make it more silent.

### IR-Receiver and Sender

This is still pretty undocumented, but the mainboard has the possibility to solder an IR-receiver and sender (e.g. very useful for Kodi or Home Automation).

If there is enough interest, Pyotek will invest some time to figure out how to enable this functionality most easily.