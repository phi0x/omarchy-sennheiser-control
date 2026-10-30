"""Remember an explicitly selected headset; retry reads/connections, never writes."""
import fcntl
import json
import os
from pathlib import Path
import re
import time

ADDRESS = re.compile(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}')

class Reconnector:
    def __init__(self, headphones, devices, state_path=None, clock=time.monotonic):
        self.headphones = headphones
        self.devices = devices
        self.path = state_path or Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state')) / 'sennheiser-control/connection.json'
        self.clock = clock
        self.target = None
        self.attempts = 0
        self.retry_at = 0
        self.error = ''
        self.lease = None
        try:
            address = json.loads(self.path.read_text()).get('address')
            if isinstance(address, str) and ADDRESS.fullmatch(address):
                self.target = address
        except (OSError, ValueError, AttributeError):
            pass

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temp = self.path.with_suffix('.tmp')
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as file:
            json.dump({'address': self.target}, file)
        temp.replace(self.path)

    def _claim(self):
        if self.lease:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        lease = self.path.with_suffix('.lock').open('a')
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lease.close()
            raise OSError('Headphone controls are open in another panel. Close that controller first.')
        self.lease = lease

    def close(self):
        self.headphones.close()
        if self.lease:
            self.lease.close()
            self.lease = None

    def connect(self, address):
        if not isinstance(address, str) or not ADDRESS.fullmatch(address):
            raise ValueError('Invalid Bluetooth address')
        # Claim ownership before changing a preference another monitor may be using.
        self._claim()
        self.target = address
        self._save()
        self.attempts = 0
        self.retry_at = 0
        return self.poll(force=True)

    def disconnect(self):
        self.target = None
        self._save()
        self.close()
        self.error = ''

    def lost(self):
        self.close()
        self.error = 'Headphone controls disconnected. Turn the headphones on; reconnecting automatically.'
        self.attempts = 0
        self.retry_at = self.clock() + 2

    def status(self):
        return dict(connected=False, reconnecting=bool(self.target), address=self.target,
                    error=self.error, retry_in=max(0, round(self.retry_at-self.clock())))

    def poll(self, force=False):
        if self.headphones.sock or not self.target:
            return
        if not force and self.clock() < self.retry_at:
            return
        try:
            known = next((d for d in self.devices() if d['address'] == self.target), None)
            if not known or not known['paired']:
                raise OSError('Pair the HDB 630 with this computer to restore headphone controls.')
            if not known.get('adapter_powered', True):
                raise OSError('Computer Bluetooth is off. Turn it on; controls will reconnect automatically.')
            self._claim()
            self.headphones.connect(self.target)
            # Validate the control connection, not merely the RFCOMM socket.
            self.headphones.get(0x0603)
            self.attempts, self.retry_at, self.error = 0, 0, ''
        except Exception as exc:
            self.close()
            self.attempts += 1
            self.retry_at = self.clock() + (2, 5, 10, 20, 30)[min(self.attempts-1, 4)]
            if 'Bluetooth is off' in str(exc) or 'Pair the HDB' in str(exc) or 'another panel' in str(exc):
                self.error = str(exc)
            else:
                self.error = 'Waiting for the headphones. Turn them on; controls will retry automatically. If they stay unavailable, disconnect your phone to free a multipoint slot.'
