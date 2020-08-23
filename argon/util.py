import os
import click


def info(message):
    click.echo(click.style(f"🛈  {message}", fg='blue'))


def error(message):
    click.echo(click.style(f"✘  {message}", fg='red'))


def warning(message):
    click.echo(click.style(f"❗  {message}", fg='yellow'))


def success(message):
    click.echo(click.style(f"✓  {message}", fg='green'))


def get_temp(vcgencmd_path: str = "/opt/vc/bin/vcgencmd", as_str=False):
    result = os.popen(f"{vcgencmd_path} measure_temp").readline().strip()
    left = "temp="
    right = "'C"
    temp = round(float(result[result.find(left) + len(left):result.find(right)]))
    if as_str:
        return f"{temp}°C"
    else:
        return temp


def prompt(question):
    while True:
        answer = input("%s [y/n]" % question).lower()
        if answer in {'y', 'ye', 'yes', 'yabbadabbado'}:
            return True
        if answer in {'n', 'no', 'nope', 'nein'}:
            return False
