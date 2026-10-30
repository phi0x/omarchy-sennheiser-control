# SPDX-License-Identifier: MIT
# Protocol port informed by hatemosphere/hdb630-control-macos; see THIRD_PARTY.md.
"""HDB 630 GAIA v3 control over a separate Bluetooth Classic connection."""
import math
import re
import socket
import struct
import subprocess
import time
from build_helper import helper_path

VENDOR = 0x0495
FILTERS = ['Gain', 'Low-pass 1', 'High-pass 1', 'All-pass 1', 'Low shelf 1',
           'High shelf 1', 'Tilt 1', 'Low-pass 2', 'High-pass 2', 'All-pass 2',
           'High shelf', 'Low shelf', 'Tilt 2', 'Bell', 'Bypass']
# key: (read, write, min, max)
SETTINGS = {
    'anc': (0x1A05, 0x1A04, 0, 1),
    'transparency': (0x1A03, 0x1A02, 0, 100),
    'crossfeed': (0x2E01, 0x2E00, 0, 2),
    'smart_pause': (0x080D, 0x080C, 0, 1),
    'on_head': (0x0401, 0x0400, 0, 1),
    'auto_answer': (0x080B, 0x080A, 0, 1),
    'sidetone': (0x0806, 0x0805, 0, 4),
    'auto_pause': (0x1801, 0x1800, 0, 1),
    'bass_boost': (0x1009, 0x1008, 0, 1),
    'comfort_call': (0x0815, 0x0814, 0, 1),
}

def packet(command, payload=b''):
    return struct.pack('>BBHHH', 0xFF, 3, len(payload), VENDOR, command) + payload

class FrameBuffer:
    def __init__(self):
        self.data = bytearray()

    def feed(self, data):
        self.data.extend(data)
        frames = []
        while len(self.data) >= 8:
            if self.data[:2] != b'\xff\x03':
                del self.data[0]
                continue
            size, vendor, cmd = struct.unpack('>HHH', self.data[2:8])
            if size > 4096:
                raise OSError('Invalid GAIA frame length')
            if len(self.data) < 8 + size:
                break
            frames.append((vendor, cmd, bytes(self.data[8:8 + size])))
            del self.data[:8 + size]
        return frames

class Headphones:
    def __init__(self):
        self.sock = None
        self.address = None
        self.frames = FrameBuffer()

    def close(self):
        if self.sock:
            self.sock.close()
        self.sock, self.address = None, None
        self.frames = FrameBuffer()

    def connect(self, address):
        if not re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', address):
            raise ValueError('Invalid Bluetooth address')
        self.close()
        helper = helper_path()
        try:
            result = subprocess.run([str(helper), address], capture_output=True, text=True, timeout=8)
        except subprocess.TimeoutExpired:
            raise OSError('Headphones are not reachable for control discovery') from None
        if result.returncode:
            raise OSError(result.stderr.strip() or 'Could not discover the HDB 630 control service')
        channel = int(result.stdout.strip())
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.settimeout(8)
        try:
            sock.connect((address, channel))
        except Exception:
            sock.close()
            raise
        self.sock, self.address = sock, address

    def request(self, command, payload=b''):
        if not self.sock:
            raise OSError('Connect the headphones first')
        try:
            self.sock.sendall(packet(command, payload))
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                self.sock.settimeout(max(.01, deadline - time.monotonic()))
                data = self.sock.recv(4096)
                if not data:
                    raise OSError('Headphone connection closed')
                for vendor, cmd, reply in self.frames.feed(data):
                    if vendor != VENDOR:
                        continue
                    if cmd == command | 0x0180:
                        raise ValueError(f'Headphones rejected command 0x{command:04x}: {reply.hex()}')
                    if cmd == command | 0x0100:
                        return reply
            raise TimeoutError(f'Headphones did not answer 0x{command:04x}')
        except OSError:
            # A late reply after timeout could be mistaken for the next request.
            self.close()
            raise

    def get(self, command, minimum=1, payload=b''):
        data = self.request(command, payload)
        if len(data) < minimum:
            raise ValueError(f'Short headphone reply for 0x{command:04x}')
        return data

    def status(self):
        values, errors = {}, {}
        reads = {'battery': 0x0603, 'charging': 0x0602, 'audio_mode': 0x0804, 'compatibility': 0x0406}
        reads.update({k: v[0] for k, v in SETTINGS.items()})
        for key, command in reads.items():
            try:
                data = self.get(command)
                values[key] = data[-1] if key == 'audio_mode' else data[0]
            except ValueError as exc:
                errors[key] = str(exc)
        try:
            timer = self.get(0x0601, 3, b'\x00')
            if timer[0] != 0:
                raise ValueError('Unexpected power timer response')
            values['auto_off'] = int.from_bytes(timer[1:3], 'big')
        except ValueError as exc:
            errors['auto_off'] = str(exc)
        fw = self.get(0x1202, 3)
        values['firmware'] = '.'.join(str(n) for n in fw[:3])
        anc = self.get(0x1A01, 6)
        values.update({{1:'anti_wind', 2:'comfort', 3:'adaptive'}.get(anc[i], f'anc_{anc[i]}'): anc[i+1]
                       for i in range(0, 6, 2)})
        return dict(connected=True, address=self.address, values=values, errors=errors)

    def set_value(self, key, value):
        if key in SETTINGS:
            _, cmd, low, high = SETTINGS[key]
            if not isinstance(value, int) or not low <= value <= high:
                raise ValueError('Setting outside allowed range')
            self.request(cmd, bytes([value]))
        elif key in ('adaptive', 'comfort', 'anti_wind'):
            high = 2 if key == 'anti_wind' else 1
            if not isinstance(value, int) or not 0 <= value <= high:
                raise ValueError('Invalid ANC value')
            self.request(0x1A00, bytes([{'anti_wind':1, 'comfort':2, 'adaptive':3}[key], value]))
        elif key == 'auto_off':
            if value not in (0, 900, 1800, 3600):
                raise ValueError('Choose Never, 15, 30 or 60 minutes')
            self.request(0x0600, b'\x00' + struct.pack('>H', value))
        elif key == 'audio_mode':
            if value not in (0, 1, 2, 4):
                raise ValueError('Unsupported audio mode')
            self.request(0x0803, bytes([0, value]))
        else:
            raise ValueError('Unknown setting')

    def peq(self):
        stages = []
        for i in range(5):
            vals = []
            for cmd, minimum in [(0x100B,3), (0x100D,3), (0x1011,3), (0x100F,2)]:
                data = self.get(cmd, minimum, bytes([i]))
                if data[0] != i:
                    raise ValueError('PEQ reply has wrong stage index')
                vals.append(data)
            stages.append(dict(frequency=int.from_bytes(vals[0][1:3], 'big'),
                               q=int.from_bytes(vals[1][1:3], 'big') / 4096,
                               gain=int.from_bytes(vals[2][1:3], 'big', signed=True) / 10,
                               filter=vals[3][1]))
        return dict(stages=stages, pregain=int.from_bytes(self.get(0x1013,2)[:2], 'big', signed=True)/10)

    def restart_resolution(self, high_resolution):
        if type(high_resolution) is not bool:
            raise ValueError('Resolution must be a boolean')
        preference = 0 if high_resolution else 1
        if self.get(0x0406)[0] == preference:
            return False
        self.request(0x0405, bytes([preference]))
        if self.get(0x0406)[0] != preference:
            raise ValueError('Headphones did not retain the resolution preference')
        try:
            self.request(0x060F)
        except OSError:
            # Restart may close RFCOMM before its acknowledgement arrives.
            pass
        return True

    def graphic_eq(self):
        gains = []
        for index in range(5):
            data = self.get(0x1002, 1, bytes([index]))
            if len(data) >= 2:
                if data[0] != index:
                    raise ValueError('Unexpected graphic EQ band')
                data = data[1:]
            gains.append(int.from_bytes(data[:1], 'big', signed=True) / 10)
        return gains

    def set_graphic_eq(self, gains):
        if len(gains) != 5 or not all(isinstance(v, (int,float)) and math.isfinite(v) and -6 <= v <= 6 for v in gains):
            raise ValueError('Graphic EQ requires five gains from -6 to +6 dB')
        for index, gain in enumerate(gains):
            self.request(0x1001, bytes([index]) + struct.pack('b', round(gain*10)))
        self.set_value('audio_mode', 1)

    def paired_devices(self):
        count = int.from_bytes(self.get(0x1400, 2)[:2], 'big')
        if count > 16:
            raise ValueError('Invalid paired-device count')
        own = self.get(0x1407)[0]
        result = []
        for index in range(count):
            data = self.get(0x1401, 3, bytes([index]))
            if data[0] != index:
                raise ValueError('Wrong paired-device index')
            result.append(dict(index=index, name=data[3:].rstrip(b'\0').decode('utf-8', 'replace'),
                               connected=bool(data[2]), own=index == own))
        return result

    @staticmethod
    def peq_commands(stages, pregain):
        # Validate the complete form before making any hardware writes.
        if len(stages) != 5 or not math.isfinite(pregain) or not -12 <= pregain <= 0:
            raise ValueError('PEQ requires five stages and pre-gain from -12 to 0 dB')
        commands = [(0x1012, struct.pack('>h', round(pregain * 10)))]
        for i, stage in enumerate(stages):
            f, q, g, t = (stage[k] for k in ('frequency', 'q', 'gain', 'filter'))
            max_q = .71 if t in (4, 5, 10, 11) else 8
            if (not all(math.isfinite(v) for v in (f,q,g,t)) or
                not 20 <= f <= 20000 or not .25 <= q <= max_q or not -12 <= g <= 12 or
                not isinstance(t, int) or t not in range(15)):
                raise ValueError(f'Invalid PEQ band {i+1}: check frequency, gain, filter and Q (shelves: Q ≤ 0.71)')
            commands.extend([(0x100E, bytes([i,t])), (0x100A, bytes([i])+struct.pack('>H',round(f))),
                             (0x100C,bytes([i])+struct.pack('>H',round(q*4096))),
                             (0x1010,bytes([i])+struct.pack('>h',round(g*10)))])
        return commands

    def set_peq(self, stages, pregain):
        for cmd, payload in self.peq_commands(stages, pregain):
            self.request(cmd, payload)
