import ctypes as C
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import io
import json
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from dongle import Dongle
from headphones import FrameBuffer, Headphones, VENDOR, packet
import service

class ProtocolTests(unittest.TestCase):
    def test_slider_write_preserves_status_message_and_identifies_quiet_operation(self):
        writes = []
        class FakeDongle:
            def status(self): return {'connected': True}
            def close(self): pass
        class FakeHeadphones:
            sock = True
            def status(self): return {'connected': True, 'values': {'transparency': 25}}
            def set_value(self, key, value): writes.append((key, value))
            def close(self): pass
        stdin = io.StringIO('{"action":"setting","key":"transparency","value":25}\n')
        stdout = io.StringIO()
        with patch.object(service, 'Dongle', FakeDongle), \
             patch.object(service, 'Headphones', FakeHeadphones), \
             patch.object(service, 'devices', return_value=[]), \
             patch.object(service.select, 'select', return_value=([stdin], [], [])), \
             patch.object(sys, 'stdin', stdin), patch.object(sys, 'stdout', stdout):
            service.run()
        frames = [json.loads(line) for line in stdout.getvalue().splitlines()]
        self.assertEqual(writes, [('transparency', 25)])
        self.assertEqual([frame['busy'] for frame in frames], [False, True, False])
        self.assertEqual(frames[1]['operation'], 'setting')
        self.assertTrue(all(frame['message'] == '' for frame in frames))
        self.assertTrue(all(frame['headphones']['connected'] for frame in frames))

    def test_gaia_fragmented_and_batched(self):
        frame = packet(0x0703, b'\x50')
        parser = FrameBuffer()
        self.assertEqual(parser.feed(b'junk' + frame[:5]), [])
        self.assertEqual(parser.feed(frame[5:] + frame), [(VENDOR, 0x0703, b'\x50')]*2)

    def test_gaia_rejects_oversized_frame(self):
        with self.assertRaises(OSError):
            FrameBuffer().feed(bytes.fromhex('ff03ffff04950703'))

    def test_gaia_matches_reply_after_notification(self):
        class FakeSocket:
            def sendall(self, data): self.sent = data
            def settimeout(self, t): pass
            def recv(self, n): return packet(0x0682, b'\x00') + packet(0x0703,b'\x55')
        hp = Headphones()
        hp.sock = FakeSocket()
        self.assertEqual(hp.request(0x0603), b'\x55')
        self.assertEqual(hp.sock.sent, bytes.fromhex('ff03000004950603'))

    def test_gaia_rejects_error_response(self):
        class FakeSocket:
            def sendall(self, data): pass
            def settimeout(self, t): pass
            def recv(self, n): return packet(0x0783,b'\x01')
        hp = Headphones()
        hp.sock = FakeSocket()
        with self.assertRaises(ValueError): hp.request(0x0603)

    def test_peq_validation_before_any_write(self):
        hp = Headphones()
        writes = []
        hp.request = lambda cmd, data: writes.append((cmd,data))
        stages = [dict(frequency=1000,q=1,gain=0,filter=13) for _ in range(5)]
        stages[-1]['q'] = 20
        with self.assertRaises(ValueError): hp.set_peq(stages, -3)
        self.assertEqual(writes, [])
        stages[-1]['q'] = 1
        stages[0]['gain'] = -2.5
        hp.set_peq(stages,-3)
        self.assertIn((0x1010, bytes.fromhex('00ffe7')),writes)
        self.assertEqual(len(writes),21)

    def test_hid_skips_notification_and_checks_lengths(self):
        class FakeHid:
            def __init__(self): self.replies=[]
            def hid_write(self, handle, data, n):
                self.replies = [bytes.fromhex('34fc020100'), bytes.fromhex('34ff060103')]
                return n
            def hid_read_timeout(self, handle, buf, n, timeout):
                if not self.replies: return 0
                data=self.replies.pop(0)
                C.memmove(buf,data,len(data))
                return len(data)
        d = Dongle.__new__(Dongle)
        d.handle = 1
        d.lib = FakeHid()
        self.assertEqual(d.command(6), b'\x03')
        with self.assertRaises(ValueError): d.command(6, b'x'*61)

    def test_live_firmware_short_masks(self):
        d = Dongle.__new__(Dongle)
        replies = {0x12: bytes.fromhex('030b00'), 1: bytes.fromhex('010301'),
                   3: b'\x04', 5: b'\x04', 6:b'\x03', 8:bytes.fromhex('0202')}
        d.command = lambda cmd: replies[cmd]
        status = d.status()
        self.assertEqual(status['firmware'], '3.11.0')
        self.assertEqual(status['codec'], 'aptX Adaptive')
        self.assertEqual(status['quality'], '24-bit / 48 kHz')

    def test_codec_validation(self):
        d = Dongle.__new__(Dongle)
        d.get = lambda cmd, n: b'\x05\x00'
        writes=[]
        d.command=lambda cmd,payload: writes.append((cmd,payload))
        with self.assertRaises(ValueError): d.set_codec(2)
        with self.assertRaises(ValueError): d.set_codec(0)
        d.set_codec(4)
        self.assertEqual(writes,[(4,b'\x04\x00')])

if __name__ == '__main__': unittest.main()
