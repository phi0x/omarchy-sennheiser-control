from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from reconnect import Reconnector

MAC = '02:00:00:00:00:01'  # Synthetic locally administered address.

class Headset:
    def __init__(self):
        self.sock = None
        self.calls = 0
        self.online = True
        self.reads = []
    def connect(self, address):
        self.calls += 1
        if not self.online:
            raise OSError('SDP connection: Host is down')
        self.sock = object()
    def get(self, cmd):
        self.reads.append(cmd)
        return b'\x50'
    def close(self): self.sock = None

class ReconnectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'connection.json'
        self.now = 0
        self.known = [dict(address=MAC, paired=True, adapter_powered=True)]
        self.hp = Headset()
        self.manager = self.make(self.hp)
        self.addCleanup(self.manager.close)
    def make(self, hp):
        return Reconnector(hp, lambda:self.known, self.path, clock=lambda:self.now)
    def test_power_cycle_recovers_without_repair_or_setting_writes(self):
        self.manager.connect(MAC)
        self.hp.online = False
        self.manager.lost()
        self.now = 2
        self.manager.poll()
        self.assertTrue(self.manager.status()['reconnecting'])
        self.assertNotIn('SDP', self.manager.status()['error'])
        calls = self.hp.calls
        self.manager.poll()
        self.assertEqual(self.hp.calls, calls)
        self.hp.online = True
        self.now += 5
        self.manager.poll()
        self.assertIsNotNone(self.hp.sock)
        self.assertEqual(self.manager.error, '')
        self.assertEqual(self.hp.reads, [0x0603, 0x0603])
    def test_adapter_off_skips_discovery_then_recovers(self):
        self.known[0]['adapter_powered'] = False
        self.manager.connect(MAC)
        self.assertEqual(self.hp.calls, 0)
        self.assertIn('Bluetooth is off', self.manager.error)
        self.known[0]['adapter_powered'] = True
        self.now += 5
        self.manager.poll()
        self.assertIsNotNone(self.hp.sock)
    def test_restart_remembers_target_and_disconnect_cancels_it(self):
        self.manager.connect(MAC)
        self.manager.close()
        second = self.make(Headset())
        self.addCleanup(second.close)
        self.assertEqual(second.target, MAC)
        second.poll()
        self.assertIsNotNone(second.headphones.sock)
        second.disconnect()
        self.now += 100
        second.poll()
        self.assertIsNone(second.headphones.sock)
        self.assertIsNone(self.make(Headset()).target)
    def test_second_monitor_does_not_open_another_connection(self):
        self.manager.connect(MAC)
        hp = Headset()
        second = self.make(hp)
        self.addCleanup(second.close)
        second.poll()
        self.assertEqual(hp.calls, 0)
        self.assertIn('another panel', second.error)
    def test_missing_pairing_does_not_repair_or_probe(self):
        self.known[0]['paired'] = False
        self.manager.connect(MAC)
        self.assertEqual(self.hp.calls, 0)
        self.assertIn('Pair the HDB', self.manager.error)
    def test_invalid_address_does_not_overwrite_remembered_target(self):
        self.manager.connect(MAC)
        with self.assertRaises(ValueError): self.manager.connect('invalid')
        self.assertEqual(self.manager.target, MAC)

if __name__ == '__main__': unittest.main()
