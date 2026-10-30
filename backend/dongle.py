# SPDX-License-Identifier: LGPL-2.1-only
# Protocol implementation informed by sobalap/btd700ctl; see THIRD_PARTY.md.
"""BTD 700 HID protocol. See THIRD_PARTY.md for protocol sources."""
import ctypes as C
import ctypes.util
import time

CODECS = ['SBC', 'aptX', 'aptX Adaptive', 'aptX Lossless', 'aptX Lite', 'LC3']
MODES = ['High quality', 'Low latency', 'Broadcast']
TRANSPORTS = ['Disconnected', 'Bluetooth Classic', 'LE Audio', 'Multipoint']

class DeviceInfo(C.Structure):
    pass
DeviceInfo._fields_ = [
    ('path', C.c_char_p), ('vendor_id', C.c_ushort), ('product_id', C.c_ushort),
    ('serial', C.c_wchar_p), ('release', C.c_ushort), ('manufacturer', C.c_wchar_p),
    ('product', C.c_wchar_p), ('usage_page', C.c_ushort), ('usage', C.c_ushort),
    ('interface', C.c_int), ('next', C.POINTER(DeviceInfo)), ('bus', C.c_int)]

class Dongle:
    def __init__(self):
        self.handle = None
        self.lib = C.CDLL(ctypes.util.find_library('hidapi-hidraw') or 'libhidapi-hidraw.so')
        signatures = {
            'hid_enumerate': ([C.c_ushort, C.c_ushort], C.POINTER(DeviceInfo)),
            'hid_free_enumeration': ([C.POINTER(DeviceInfo)], None),
            'hid_open_path': ([C.c_char_p], C.c_void_p),
            'hid_close': ([C.c_void_p], None),
            'hid_write': ([C.c_void_p, C.c_void_p, C.c_size_t], C.c_int),
            'hid_read_timeout': ([C.c_void_p, C.c_void_p, C.c_size_t, C.c_int], C.c_int),
            'hid_error': ([C.c_void_p], C.c_wchar_p),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.lib, name)
            fn.argtypes, fn.restype = args, result

    def connect(self):
        if self.handle:
            return
        devices = self.lib.hid_enumerate(0x3542, 0x3001)
        current = devices
        found = False
        try:
            while current:
                info = current.contents
                if info.usage_page == 0xFFA2 and info.usage == 1:
                    found = True
                    self.handle = self.lib.hid_open_path(info.path)
                    if self.handle:
                        return
                current = info.next
        finally:
            self.lib.hid_free_enumeration(devices)
        if found:
            raise PermissionError('BTD 700 needs device access. Run ./install.sh --device-access once.')
        raise OSError('BTD 700 not found. Plug in the dongle and retry.')

    def close(self):
        if self.handle:
            self.lib.hid_close(self.handle)
            self.handle = None

    def command(self, command, payload=b''):
        if len(payload) > 60:
            raise ValueError('HID payload exceeds 60 bytes')
        self.connect()
        # Drain old notifications/responses before issuing a new request.
        buf = C.create_string_buffer(64)
        for _ in range(64):
            if self.lib.hid_read_timeout(self.handle, buf, 64, 0) <= 0:
                break
        packet = bytes([0x34, 0xFE, command, len(payload)]) + payload
        data = C.create_string_buffer(packet.ljust(64, b'\0'), 64)
        if self.lib.hid_write(self.handle, data, 64) != 64:
            self.close()
            raise OSError('Could not write to BTD 700')
        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            count = self.lib.hid_read_timeout(self.handle, buf, 64, 100)
            if count < 0:
                self.close()
                raise OSError('BTD 700 disconnected')
            if count >= 4:
                reply = buf.raw[:count]
                if reply[:3] == bytes([0x34, 0xFF, command]):
                    size = reply[3]
                    if size > count - 4:
                        raise OSError('Truncated dongle response')
                    return reply[4:4 + size]
        raise TimeoutError(f'BTD 700 did not answer command 0x{command:02x}')

    def get(self, command, minimum):
        data = self.command(command)
        if len(data) < minimum:
            raise OSError(f'Short response to dongle command 0x{command:02x}')
        return data

    def status(self):
        fw = self.get(0x12, 3)
        cfg = self.get(1, 2)
        state = self.get(6, 1)[0]
        supported = int.from_bytes(self.get(3, 1)[:2], 'little')
        codec = int.from_bytes(self.get(5, 1)[:2], 'little')
        quality = self.get(8, 2)
        name = lambda seq, n: seq[n] if n < len(seq) else f'Unknown ({n})'
        return dict(connected=True, firmware=f'{fw[0]}.{fw[1]}.{int.from_bytes(fw[2:4], "little")}',
                    mode=cfg[0], transport=cfg[1], transport_name=name(TRANSPORTS, cfg[1]),
                    state=name(['Idle', 'Disconnected', 'Connected', 'Playing audio', 'Microphone active'], state),
                    codec=', '.join(c for i, c in enumerate(CODECS) if codec & (1 << i)) or 'No active codec',
                    supported=supported,
                    quality=f'{name(["Unknown", "16-bit", "24-bit"], quality[0])} / {name(["Unknown", "44.1 kHz", "48 kHz", "96 kHz"], quality[1])}')

    def set_mode(self, mode, transport):
        if mode not in range(3) or transport not in (1, 2, 3):
            raise ValueError('Invalid audio mode or transport')
        self.command(2, bytes([mode, transport]))

    def set_codec(self, mask):
        supported = int.from_bytes(self.get(3, 1)[:2], 'little')
        if not mask or mask & ~supported:
            raise ValueError('Codec is not supported by this dongle')
        self.command(4, mask.to_bytes(2, 'little'))

    def broadcast(self):
        data = self.get(0x09, 3)
        name = self.command(0x0D).split(b'\0', 1)[0].decode('utf-8', 'replace')
        return dict(public=bool(data[0]), quality=data[1], encrypted=bool(data[2]), name=name)

    def set_broadcast(self, name, public, quality, encrypted, password=None):
        if not isinstance(name, str) or '\0' in name or not 1 <= len(name.encode('utf-8')) <= 32:
            raise ValueError('Broadcast name must contain 1–32 UTF-8 bytes')
        if type(public) is not bool or type(encrypted) is not bool or type(quality) is not int or quality not in (0,1,2):
            raise ValueError('Invalid broadcast settings')
        if password is not None and (not isinstance(password, str) or
                                     not 1 <= len(password.encode('utf-8')) <= 16 or '\0' in password):
            raise ValueError('Broadcast password must contain 1–16 UTF-8 bytes')
        current = self.broadcast()
        if encrypted and not current['encrypted'] and password is None:
            raise ValueError('Enter a password when enabling encryption')
        # Validate everything first; do not read or publish the existing password.
        self.command(0x0E, name.encode('utf-8') + b'\0')
        if password is not None:
            self.command(0x0C, password.encode('utf-8'))
        self.command(0x0A, bytes([int(public), quality, int(encrypted)]))
