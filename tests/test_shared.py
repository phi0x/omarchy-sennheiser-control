import json
import multiprocessing
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from shared import Broker

class SharedControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        worker = self.root/'fake-worker.py'
        worker.write_text('''import os,sys,json
state={'headphones':{'connected':True},'pid':os.getpid(),'count':0}
print(json.dumps(state),flush=True)
for line in sys.stdin:
 request=json.loads(line)
 state['count']+=1
 state['last']=request['action']
 print(json.dumps(state),flush=True)
''')
        command = [sys.executable, '-u', str(worker)]
        self.server = multiprocessing.Process(target=Broker(self.root,command).serve)
        self.server.start()
        self.addCleanup(self.stop)
        self.clients=[]
    def stop(self):
        for sock, stream in self.clients:
            stream.close(); sock.close()
        self.server.join(5)
        if self.server.is_alive():
            self.server.terminate();self.server.join(2)
    def connect(self):
        deadline=time.monotonic()+3
        while True:
            sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            sock.settimeout(2)
            try:
                sock.connect(str(self.root/'control.sock'));break
            except (FileNotFoundError,ConnectionRefusedError):
                sock.close()
                if time.monotonic()>deadline:raise
                time.sleep(.01)
        stream=sock.makefile('rb')
        pair=(sock,stream)
        self.clients.append(pair)
        return pair
    def read(self,pair): return json.loads(pair[1].readline())
    def test_both_monitors_share_status_commands_and_one_worker(self):
        first=self.connect();a=self.read(first)
        second=self.connect();b=self.read(second)
        self.assertEqual(a,b)
        self.assertTrue(b['headphones']['connected'])
        second[0].sendall(b'{"action":"from-secondary"}\n')
        a,b=self.read(first),self.read(second)
        self.assertEqual(a,b)
        self.assertEqual(a['count'],1)
        self.assertEqual(a['last'],'from-secondary')
        first[0].sendall(b'{"action":"one"}\n{"action":"two"}\n')
        for count in (2,3):
            a,b=self.read(first),self.read(second)
            self.assertEqual(a,b)
            self.assertEqual(a['count'],count)
        first[1].close();first[0].close();self.clients.remove(first)
        second[0].sendall(b'{"action":"still-connected"}\n')
        self.assertEqual(self.read(second)['count'],4)
        second[1].close();second[0].close();self.clients.remove(second)
        self.server.join(5)
        self.assertEqual(self.server.exitcode,0)
        self.assertFalse((self.root/'control.sock').exists())
    def test_invalid_requests_do_not_break_other_monitor(self):
        first=self.connect();self.read(first)
        first[0].sendall(b'invalid-json\n[]\n{"action":"refresh"}\n')
        state=self.read(first)
        self.assertEqual(state['count'],1)
        self.assertEqual(state['last'],'refresh')
    def test_duplicate_broker_does_not_replace_live_socket(self):
        first=self.connect();a=self.read(first)
        other=multiprocessing.Process(target=Broker(self.root).serve)
        other.start();other.join(2)
        self.assertEqual(other.exitcode,0)
        second=self.connect()
        self.assertEqual(self.read(second)['pid'],a['pid'])

if __name__=='__main__':unittest.main()
