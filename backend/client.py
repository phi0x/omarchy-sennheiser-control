#!/usr/bin/python
"""Stdio proxy: each monitor attaches to the same session controller."""
import os
from pathlib import Path
import selectors
import socket
import subprocess
import sys
import time
from shared import runtime_dir


def attach():
    directory = runtime_dir()
    path = directory/'control.sock'
    launched = False
    for _ in range(100):
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            client.connect(str(path))
            return client
        except (FileNotFoundError, ConnectionRefusedError):
            client.close()
            if not launched:
                process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).with_name('shared.py'))],
                                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL, start_new_session=True)
                launched = True
            time.sleep(.05)
    raise OSError('Could not start the shared headphone controller')


def run():
    with attach() as client, selectors.DefaultSelector() as selector:
        selector.register(sys.stdin, selectors.EVENT_READ, 'input')
        selector.register(client, selectors.EVENT_READ, 'controller')
        while True:
            for key, _ in selector.select():
                if key.data == 'input':
                    data = os.read(sys.stdin.fileno(), 65536)
                    if not data:
                        return
                    client.sendall(data)
                else:
                    data = client.recv(65536)
                    if not data:
                        return
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()

if __name__ == '__main__':
    run()
