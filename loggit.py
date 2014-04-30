#!/usr/bin/python3
# vim: set fileencoding=utf-8 :
#
# Module to commit logs to a remote git server
#
# Requires the plumbum module, available via pip3
# Requires a git repository to already exist on the server at the specified path.
# Requires a git repository to already exist on the local host at the specified path.
# Requires the local user account to have git privileges in the local log path.
# Requires the local root account to have an entry in /root/.ssh/config to use
#   the local user account's id_rsa file when connecting to the server.
# Each commit takes approximately 0.27 seconds.

__author__ = 'Edwin Sheldon <eas604@jagmail.southalabama.edu'

import plumbum
import uuid
import argparse
import sys
import logging
import signal
import time


def commit(directory, user, host, remote_path):
    """Create a new git commit from the specified directory, the push it to the remote host."""
    start_time = time.time()

    # Commit message will be a GUID
    msg = uuid.uuid4()
    git = plumbum.local['/usr/bin/git']

    # cd to the log directory
    plumbum.local.cwd = directory

    try:
        # Get our local changes. Commit message is a GUID.
        git['add', '.']()
        git['commit', '-m', str(msg)]()
    except:
        logging.info('No changes since last commit. Aborting.')
        return

    try:
        # push our changes
        git['push', 'origin', 'master']()
    except:
        logging.error('Failed to commit changeset: {}'.format(msg))
        raise

    logging.info('Changeset committed: {0} {1}'.format(msg, time.time() - start_time))


def create_remote(directory, user, host, remote_path):
    """Create a `remote` to connect to our repository"""
    git = plumbum.local['/usr/bin/git']

    # cd to the log directory
    plumbum.local.cwd = directory

    try:
        git['remote', 'rm', 'origin']()
    except:
        # origin remote does not yet exist
        pass

    try:
        # ensure we have a remote pointing to the specified host
        args = ['remote', 'add', 'origin', '{0}@{1}:{2}'.format(user, host, remote_path)]
        git[args]()
    except:
        logging.error('Failed to create git remote: {}'.format(host))
        raise


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

    logging.info('Signal received: {0} {1}'.format(str_sig, frame))
    sys.exit(0)


def run(directory, user, host, remote_path, interval_seconds=5):
    """Continuously call commit() after every specified interval, in seconds."""

    # Ensure we have a remote pointing to the server
    create_remote(directory, user, host, remote_path)

    # Watch for certain signals, and terminate when received
    for sig in (signal.SIGINT, signal.SIGQUIT, signal.SIGTERM):
        signal.signal(sig, signal_handler)

    while True:
        find_log_tampering(directory)
        commit(directory, user, host, remote_path)
        if interval_seconds > 0:
            time.sleep(interval_seconds)


def find_log_tampering(directory):
    """Search for lines that may have been tampered since last commit."""
    plumbum.local.cwd = directory
    git = plumbum.local['/usr/bin/git']
    diff = git['diff', '--no-prefix']()
    lines = [line.rstrip() for line in diff.split('\n')]
    last_file = None

    for line in lines:
        # A change to a file will begin with --- or +++
        if line.startswith('---') or line.startswith('+++'):
            last_file = line[4:].rstrip()

        # Check for removed lines.
        # In a diff, when a line is removed, it starts with '-', followed by the line contents.
        # Incidentally, this will also catch altered lines: an altered line is first removed, 
        # then the new line added.
        if line.startswith('-') and not line.startswith('---'):
            # Possible removed line
            msg = 'DELETED | {0} {1}'.format(last_file, line)
            logging.warning(msg)


def main():
    """Parse arguments and call commit()"""
    parser = argparse.ArgumentParser(description='Use git to synchronize logs to a remote server')
    parser.add_argument('user', type=str, help='remote user account')
    parser.add_argument('host', type=str, help='destination hostname')
    parser.add_argument('local_path', type=str, help='local repository to push')
    parser.add_argument('remote_path', type=str, help='remote repository to which logs are pushed')
    parser.add_argument('-i', dest='interval', type=float, help='loop interval, in seconds')

    args = parser.parse_args()

    # logging init
    fmt = '%(asctime)s %(levelname)s > %(message)s'
    formatter = logging.Formatter(fmt)
    logging.basicConfig(filename='{}/loggit.log'.format(args.local_path), format=fmt)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if args.interval is None:
        run(args.local_path, args.user, args.host, args.remote_path)
    else:
        run(args.local_path, args.user, args.host, args.remote_path, args.interval)


if __name__ == '__main__':
    main()
