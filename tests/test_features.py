import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from headphones import Headphones
from dongle import Dongle
from presets import Presets

class FeatureTests(unittest.TestCase):
    def test_graphic_eq_validates_all_bands_and_encodes_signed_gains(self):
        hp=Headphones();writes=[]
        hp.request=lambda c,p=b'':writes.append((c,p))
        with self.assertRaises(ValueError):hp.set_graphic_eq([0,0,0,0,7])
        self.assertFalse(writes)
        hp.set_graphic_eq([-2.5,0,1,2,3])
        self.assertEqual(writes[0],(0x1001,b'\x00\xe7'))
        self.assertEqual(writes[-1],(0x0803,b'\x00\x01'))
        self.assertEqual(len(writes),6)

    def test_power_and_wind_encodings(self):
        hp=Headphones();writes=[]
        hp.request=lambda c,p=b'':writes.append((c,p))
        hp.set_value('auto_off',1800);hp.set_value('anti_wind',2);hp.set_value('sidetone',4)
        self.assertEqual(writes,[(0x0600,b'\x00\x07\x08'),(0x1A00,b'\x01\x02'),(0x0805,b'\x04')])
        with self.assertRaises(ValueError):hp.set_value('auto_off',2000)
        with self.assertRaises(ValueError):hp.set_value('sidetone',5)
        self.assertEqual(len(writes),3)
    def test_resolution_verifies_preference_before_restart(self):
        hp=Headphones();writes=[];read=iter([b'\x01',b'\x00'])
        hp.get=lambda cmd:next(read)
        hp.request=lambda c,p=b'':writes.append((c,p))
        self.assertTrue(hp.restart_resolution(True))
        self.assertEqual(writes,[(0x0405,b'\x00'),(0x060F,b'')])
        hp.get=lambda cmd:b'\x00';writes.clear()
        self.assertFalse(hp.restart_resolution(True));self.assertFalse(writes)
    def test_resolution_does_not_restart_after_failed_verification(self):
        hp=Headphones();writes=[]
        hp.get=lambda cmd:b'\x01'
        hp.request=lambda c,p=b'':writes.append((c,p))
        with self.assertRaises(ValueError):hp.restart_resolution(True)
        self.assertEqual(writes,[(0x0405,b'\x00')])
    def test_read_only_paired_list_marks_own_connection(self):
        hp=Headphones()
        replies={0x1400:b'\x00\x02',0x1407:b'\x01'}
        hp.get=lambda c,minimum=1,payload=b'':replies[c] if c in replies else payload+b'\x00\x01'+(b'Phone' if payload==b'\x00' else b'Computer')
        result=hp.paired_devices()
        self.assertEqual([x['own'] for x in result],[False,True])
        self.assertEqual(result[1]['name'],'Computer')
    def test_broadcast_validation_before_writes_and_password_not_exposed(self):
        d=Dongle.__new__(Dongle);writes=[]
        d.get=lambda c,n:b'\x01\x02\x01'
        d.command=lambda c,p=b'': b'My room\0' if c==0x0D else writes.append((c,p))
        self.assertNotIn('password',d.broadcast())
        d.set_broadcast('Room',True,2,True,None)
        self.assertEqual(writes,[(0x0E,b'Room\0'),(0x0A,b'\x01\x02\x01')])
        writes.clear()
        for args in [('x'*33,True,2,True,None),('Room',True,1.0,True,None),('Room',True,2,True,'é'*9)]:
            with self.assertRaises(ValueError):d.set_broadcast(*args)
        self.assertFalse(writes)
        d.set_broadcast('Room',False,1,True,'secret')
        self.assertEqual(writes[1],(0x0C,b'secret'))
    def test_new_encryption_requires_password(self):
        d=Dongle.__new__(Dongle);d.broadcast=lambda:dict(encrypted=False)
        d.command=lambda *a:self.fail('Should validate before writes')
        with self.assertRaises(ValueError):d.set_broadcast('Room',True,2,True)
    def test_presets_save_load_replace_and_delete_without_hardware(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Presets(Path(temp)/'presets.json')
            stages=[dict(frequency=1000,q=1,gain=0,filter=13) for _ in range(5)]
            p.save('My preset',stages,-3)
            self.assertEqual(p.names(),['My preset'])
            self.assertEqual(p.load('My preset')['pregain'],-3)
            p.save('My preset',stages,-6)
            self.assertEqual(p.load('My preset')['pregain'],-6)
            stages[-1]['q']=999
            with self.assertRaises(ValueError):p.save('Bad',stages,0)
            self.assertEqual(p.names(),['My preset'])
            p.delete('My preset');self.assertEqual(p.names(),[])

if __name__=='__main__':unittest.main()
