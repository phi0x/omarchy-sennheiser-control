"""Idle maintenance must not repeatedly query devices during audio playback."""
import ctypes as C
import io
import json
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from dongle import DeviceInfo, Dongle
from headphones import Headphones, packet
import service


class PassiveTransportTests(unittest.TestCase):
    def headset(self):
        host, peer = socket.socketpair()
        host.settimeout(2)
        peer.setblocking(False)
        hp = Headphones()
        hp.sock = host
        self.addCleanup(hp.close)
        self.addCleanup(peer.close)
        return hp, peer

    def test_idle_socket_check_sends_nothing_and_detects_disconnect(self):
        hp, peer = self.headset()
        self.assertTrue(hp.poll_connection())
        with self.assertRaises(BlockingIOError):
            peer.recv(4096)
        peer.close()
        self.assertFalse(hp.poll_connection())
        self.assertIsNone(hp.sock)
        self.assertFalse(hp.poll_connection())

    def test_notifications_are_drained_without_commands_or_losing_fragments(self):
        hp, peer = self.headset()
        notification = packet(0x0682, b'\x00')
        peer.sendall(notification[:5])
        self.assertTrue(hp.poll_connection())
        self.assertEqual(hp.frames.data, notification[:5])
        peer.sendall(notification[5:])
        self.assertTrue(hp.poll_connection())
        self.assertFalse(hp.frames.data)
        with self.assertRaises(BlockingIOError):
            peer.recv(4096)

    def test_dongle_presence_uses_enumeration_without_opening_or_writing(self):
        info = DeviceInfo()
        info.usage_page, info.usage = 0xFFA2, 1
        library = Mock(spec=['hid_enumerate', 'hid_free_enumeration'])
        library.hid_enumerate.return_value = C.pointer(info)
        dongle = Dongle.__new__(Dongle)
        dongle.lib = library
        self.assertTrue(dongle.is_present())
        library.hid_enumerate.assert_called_once_with(0x3542, 0x3001)
        library.hid_free_enumeration.assert_called_once()
        info.usage_page = 0xFF00
        self.assertFalse(dongle.is_present())
        library.hid_enumerate.return_value = C.POINTER(DeviceInfo)()
        self.assertFalse(dongle.is_present())


class IdleServiceTests(unittest.TestCase):
    def setUp(self):
        self.dongle = Mock()
        self.dongle.is_present.return_value = True
        self.dongle.status.return_value = {'connected': True, 'state': 'Playing audio'}
        self.hp = Mock()
        self.hp.sock = object()
        self.hp.poll_connection.return_value = True
        self.hp.status.return_value = {'connected': True, 'values': {'battery': 80}}
        self.reconnect = Mock()
        self.reconnect.status.return_value = {'connected': False, 'reconnecting': True}
        self.presets = Mock()
        self.presets.names.return_value = []
        self.presets.load.return_value = {'stages': [], 'pregain': -3}

    def run_worker(self, requests, events):
        stdin = io.StringIO(''.join(json.dumps(r) + '\n' for r in requests))
        stdout = io.StringIO()
        sequence = iter(events)

        def readiness(*args):
            event = next(sequence)
            if callable(event):
                event()
                event = False
            return ([stdin] if event else [], [], [])

        with patch.object(service, 'Dongle', return_value=self.dongle), \
             patch.object(service, 'Headphones', return_value=self.hp), \
             patch.object(service, 'Reconnector', return_value=self.reconnect), \
             patch.object(service, 'Presets', return_value=self.presets), \
             patch.object(service, 'devices', return_value=[]), \
             patch.object(service.select, 'select', side_effect=readiness), \
             patch.object(sys, 'stdin', stdin), patch.object(sys, 'stdout', stdout):
            service.run()
        return [json.loads(line) for line in stdout.getvalue().splitlines()]

    def test_idle_ticks_keep_cached_values_without_bulk_reads(self):
        frames = self.run_worker([], [False, False, False, True])
        self.dongle.status.assert_called_once()
        self.hp.status.assert_called_once()
        self.assertEqual(self.hp.poll_connection.call_count, 3)
        self.assertTrue(all(f['headphones']['values']['battery'] == 80 for f in frames))

    def test_explicit_refresh_still_reads_both_devices(self):
        self.run_worker([{'action': 'refresh'}], [False, True, False, True])
        self.assertEqual(self.dongle.status.call_count, 2)
        self.assertEqual(self.hp.status.call_count, 2)

    def test_local_preset_actions_do_not_query_devices(self):
        requests = [{'action': 'preset_save', 'name': 'Draft', 'stages': [], 'pregain': -3},
                    {'action': 'preset_load', 'name': 'Draft'},
                    {'action': 'preset_delete', 'name': 'Draft'}]
        frames = self.run_worker(requests, [True, True, True, True])
        self.dongle.status.assert_called_once()
        self.hp.status.assert_called_once()
        self.assertEqual(frames[-1]['peq_revision'], 1)
        self.assertEqual(frames[-1]['peq']['pregain'], -3)

    def test_plugin_update_check_does_not_read_hardware(self):
        result = {'status': 'update-available', 'latest': '0.1.2'}
        with patch.object(service, 'check_plugin_updates', return_value=result) as check:
            frames = self.run_worker([{'action': 'plugin_update_check'}], [True, True])
        check.assert_called_once_with(frames[-1]['plugin']['version'])
        self.assertEqual(frames[-1]['plugin_update'], result)
        self.dongle.status.assert_called_once()
        self.hp.status.assert_called_once()

    def test_passive_loss_invalidates_eq_and_reconnect_reads_once(self):
        online = True
        def disconnect():
            nonlocal online
            online = False
        def check_connection():
            if not online:
                self.hp.sock = None
            return self.hp.sock is not None
        def reconnect():
            nonlocal online
            online = True
            self.hp.sock = object()
        self.hp.poll_connection.side_effect = check_connection
        self.presets.load.return_value = {'stages': [], 'pregain': -3}
        attempts = iter([None, None, None, reconnect, None])
        def poll():
            attempt = next(attempts)
            if attempt:
                attempt()
        self.reconnect.poll.side_effect = poll
        frames = self.run_worker([{'action': 'preset_load', 'name': 'Draft'}],
                                 [True, disconnect, False, False, True])
        self.assertFalse(frames[3]['headphones']['connected'])
        self.assertNotIn('peq', frames[3])
        self.assertTrue(frames[-1]['headphones']['connected'])
        self.assertEqual(self.hp.status.call_count, 2)
        self.reconnect.lost.assert_called_once()

    def test_usb_unplug_and_replug_refresh_only_on_return(self):
        def unplug(): self.dongle.is_present.return_value = False
        def replug(): self.dongle.is_present.return_value = True
        frames = self.run_worker([], [unplug, replug, False, True])
        self.assertFalse(frames[1]['dongle']['connected'])
        self.assertTrue(frames[-1]['dongle']['connected'])
        self.assertEqual(self.dongle.status.call_count, 2)


if __name__ == '__main__':
    unittest.main()
