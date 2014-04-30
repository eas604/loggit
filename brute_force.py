#!/usr/bin/python3
# vim: set fileencoding=utf-8 :
#
# Module to simulate a brute force password attack, simply by writing failures to /var/log/auth.log
#

__author__ = 'Edwin Sheldon <eas604@jagmail.southalabama.edu'

import datetime
import socket
import random
import sys
import signal
import time
import argparse


def ssh_message():
    """Create a message simulating a failed SSH login attempt for writing to /var/log/auth.log"""
    # Sample message:
    # Apr 27 02:20:28 server sshd[10587]: Failed password for root from 10.0.10.1 port 46899 ssh2
    dte = datetime.datetime.now().strftime('%b %d %Y %H:%M:%S')
    host = socket.gethostname()
    pid = random.randrange(5000, 10000)

    # standard Linux ephemeral port range below
    port = random.randrange(32768, 61000)

    ds = '{0} {1} sshd[{2}]: Failed password for root from 10.0.10.1 port {3} ssh2'.format(dte, host, pid, port)
    return ds


def signal_handler(sig, frame):
    """Halt processing on certain signals."""
    if sig == 2:
        str_sig = 'SIGINT'
    elif sig == 3:
        str_sig = 'SIGQUIT'
    elif sig == 15:
        str_sig = 'SIGTERM'
    else:
        str_sig = str(sig)

    print('Signal received: {0} {1}'.format(str_sig, frame))
    sys.exit(0)


def write_log(path):
    """Write a fake SSH login failure to the given path"""
    msg = ssh_message()
    try:
        with open(path, 'a') as fle:
            fle.write('{}\n'.format(msg))
            print(msg)
    except (IOError, OSError):
        print('Failed to write to {}'.format(path))
        raise


def run(path, interval_seconds=1):
    """Spam failed SSH logins to /var/log/auth.log until terminated."""
    # Watch for certain signals, and terminate when received
    for sig in (signal.SIGINT, signal.SIGQUIT, signal.SIGTERM):
        signal.signal(sig, signal_handler)

    while True:
        write_log(path)
        time.sleep(interval_seconds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Write a fake SSH login failure to the given path')
    parser.add_argument('local_path', type=str, help='local file to write')
    parser.add_argument('-i', type=float, dest='interval', help='loop interval, in seconds')
    args = parser.parse_args()

    if args.interval is None:
        run(args.local_path)
    else:
        run(args.local_path, args.interval)