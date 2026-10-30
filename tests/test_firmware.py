from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import firmware

class FirmwareTests(unittest.TestCase):
    def test_numeric_versions_and_current_devices(self):
        def catalog(url):
            return {'success':True,'data':['3.9.0','3.11.0']} if '700434' in url else {'success':True,'data':['3.33.3']}
        result=firmware.check({'dongle':'3.11.0','headphones':'3.33.3'},catalog)
        self.assertTrue(all(x['status']=='up-to-date' for x in result['devices'].values()))
    def test_new_release_unknown_device_and_no_downgrade(self):
        catalog=lambda url:{'success':True,'data':['3.11.0']}
        result=firmware.check({'dongle':'3.9.0'},catalog)
        self.assertEqual(result['devices']['dongle']['status'],'update-available')
        self.assertEqual(result['devices']['headphones']['status'],'connect-device')
        result=firmware.check({'dongle':'4.0.0'},catalog)
        self.assertEqual(result['devices']['dongle']['status'],'newer-than-catalog')
    def test_unavailable_or_malformed_catalog_is_never_up_to_date(self):
        for data in [[],{'data':[]},{'success':False,'data':['3.11.0']},{'success':True,'data':[]},{'success':True,'data':['unknown']}]:
            result=firmware.check({'dongle':'3.11.0'},lambda url:data)
            self.assertEqual(result['devices']['dongle']['status'],'check-failed')
        def offline(url):raise OSError('offline')
        result=firmware.check({'dongle':'3.11.0'},offline)
        self.assertEqual(result['devices']['dongle']['status'],'check-failed')
    def test_redirect_does_not_accept_third_party_catalog(self):
        class Reply:
            url='https://example.com/catalog'
            def __enter__(self):return self
            def __exit__(self,*args):pass
        with patch.object(firmware.urllib.request,'urlopen',return_value=Reply()):
            with self.assertRaises(ValueError):firmware.get_json(firmware.ROOT)
    def test_checker_only_requests_public_product_metadata(self):
        urls=[]
        def catalog(url):
            urls.append(url)
            return {'success':True,'data':['3.11.0']}
        firmware.check({'dongle':'3.11.0','headphones':'3.33.3'},catalog)
        self.assertEqual(len(urls),2)
        self.assertTrue(all(url.startswith('https://api.s-consumer-cloud.com/firmware/api/v2/availableSystemReleases/') for url in urls))
        self.assertNotIn('3.33.3',''.join(urls))

if __name__=='__main__':unittest.main()
