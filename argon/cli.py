#!/usr/bin/env python3

import logging
import os
import sys
from pathlib import Path

import click

VERSION = '0.1.0'

script_dir = Path(__file__).parent.absolute()
home_dir = script_dir.parent
os.chdir(home_dir)

from argon.util import get_temp
from argon.argon import Argon


@click.group()
@click.option('--verbose', default=False, is_flag=True,
              help='enable verbose for debugging purposes (sets log level to DEBUG)')
@click.option('--config', default=f"{home_dir}/config.ini", type=str,
              help='path to config file')
@click.pass_context
def cli(ctx, verbose: bool, config: str):
    logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.DEBUG if verbose else logging.INFO)
    logging.info(f"Started Open Argon. Home directory: {home_dir}")

    ctx.obj = Argon(config, verbose)

    def last_resort(type, value, tb):
        if type is KeyboardInterrupt:
            logging.warning("Stopped by keyboard interrupt.")
        else:
            logging.error(f"Unhandled error!", exc_info=(type, value, tb))

    sys.excepthook = last_resort


@cli.command()
@click.pass_obj
def doctor(argon):
    """Run interactive checks to verify hardware and software functionality.
    """
    argon.doctor()


@cli.command()
def temp():
    """Print the detected temperature to stdout.
    """
    print(get_temp(as_str=True))


@click.argument('speed', type=int, nargs=1)
@cli.command()
@click.pass_obj
def fan(argon, speed: int):
    """
    Set fan SPEED. Note: Might interfere with running daemon.

    SPEED is in percent, 0 (off) to 100 (max).
    """
    argon.set_fan(speed)


@cli.command()
@click.pass_obj
def daemon(argon):
    """Start daemon/driver mode (non-forking), reacting to your button pushes
    and setting the temperature according to the chosen profile.

    Warnings:
        Running multiple daemons can cause interferences.
    """
    argon.daemon()


@cli.command()
@click.pass_obj
def config(argon):
    """Call your preferred editor for configuring CONFIG, plus other safety checks.
    Prefer this over editing the file manually."""
    argon.configure()


@cli.command('_notify-shutdown', hidden=True)
@click.pass_obj
def _notify_shutdown(argon):
    argon.notify_shutdown()


@cli.command()
@click.pass_obj
def version(argon):
    """Show version info and banner.
    """
    width, _ = argon.banner()

    info = f'By Pyotek (https://pyotek.dev)'
    ver = f'Version: {VERSION}'

    click.secho(f'{ver}{" " * (width - (len(ver) + len(info)))}{info}', fg='blue', bold=True)

    click.echo()


if __name__ == '__main__':
    cli()
