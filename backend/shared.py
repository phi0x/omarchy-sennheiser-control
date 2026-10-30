"""One hardware worker shared by all monitor widgets over a private Unix socket."""
import fcntl
import json
import os
from pathlib import Path
import selectors
import socket
import subprocess
import sys


def runtime_dir():
    parent = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp'))
    path = parent / f'sennheiser-control-{os.getuid()}'
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.stat().st_uid != os.getuid():
        raise PermissionError('Controller runtime directory belongs to another user')
    path.chmod(0o700)
    return path


class Broker:
    def __init__(self, directory, worker_command=None):
        self.directory = Path(directory)
        self.command = worker_command or [sys.executable, '-B', str(Path(__file__).with_name('service.py'))]

    def serve(self):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (self.directory/'broker.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return
            self._serve_locked()

    def _serve_locked(self):
        path = self.directory/'control.sock'
        path.unlink(missing_ok=True)
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        selector = selectors.DefaultSelector()
        clients = {}
        worker = None
        latest = b''
        output = bytearray()
        had_client = False
        def drop(client):
            selector.unregister(client)
            clients.pop(client, None)
            client.close()
        try:
            listener.bind(str(path))
            path.chmod(0o600)
            listener.listen(8)
            selector.register(listener, selectors.EVENT_READ, 'listen')
            while True:
                events = selector.select(10)
                if not events and not clients:
                    return
                for key, _ in events:
                    if key.data == 'listen':
                        client, _ = listener.accept()
                        client.settimeout(1)
                        clients[client] = bytearray()
                        selector.register(client, selectors.EVENT_READ, 'client')
                        had_client = True
                        if worker is None:
                            worker = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                      stderr=subprocess.DEVNULL, bufsize=0)
                            selector.register(worker.stdout, selectors.EVENT_READ, 'worker')
                        if latest:
                            try:
                                client.sendall(latest)
                            except OSError:
                                drop(client)
                    elif key.data == 'worker':
                        chunk = os.read(worker.stdout.fileno(), 65536)
                        if not chunk:
                            return
                        output.extend(chunk)
                        while b'\n' in output:
                            line, _, remaining = output.partition(b'\n')
                            output[:] = remaining
                            latest = bytes(line) + b'\n'
                            for client in list(clients):
                                try:
                                    client.sendall(latest)
                                except OSError:
                                    drop(client)
                    else:
                        client = key.fileobj
                        try:
                            chunk = client.recv(65536)
                        except OSError:
                            chunk = b''
                        if not chunk:
                            drop(client)
                            continue
                        buffer = clients[client]
                        buffer.extend(chunk)
                        if len(buffer) > 65536:
                            drop(client)
                            continue
                        while b'\n' in buffer:
                            line, _, remaining = buffer.partition(b'\n')
                            buffer[:] = remaining
                            try:
                                request = json.loads(line)
                                if not isinstance(request, dict) or not isinstance(request.get('action'), str):
                                    continue
                            except ValueError:
                                continue
                            payload = memoryview(bytes(line) + b'\n')
                            while payload:
                                payload = payload[worker.stdin.write(payload):]
                # The worker lives while any monitor is attached, even with popups closed.
                # Once the shell unloads every proxy, release hardware and exit.
                if had_client and not clients:
                    return
        finally:
            for client in list(clients):
                client.close()
            selector.close()
            listener.close()
            if worker:
                worker.stdin.close()
                try:
                    worker.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    worker.terminate()
                    try:
                        worker.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        worker.kill()
                        worker.wait()
                worker.stdout.close()
            path.unlink(missing_ok=True)

if __name__ == '__main__':
    Broker(runtime_dir()).serve()
