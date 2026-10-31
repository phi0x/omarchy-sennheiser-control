import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
import plugin_updates as updates


def release(tag='v0.1.1', **extra):
    return dict(tag_name=tag, draft=False, prerelease=False, **extra)


class PluginUpdateTests(unittest.TestCase):
    def test_numeric_versions_and_all_comparison_states(self):
        for installed, tag, status in [
            ('0.1.1', 'v0.1.1', 'up-to-date'),
            ('0.1.9', 'v0.1.10', 'update-available'),
            ('0.2.0', '0.1.1', 'newer-than-release'),
            (None, 'v0.1.1', 'unknown-installed'),
        ]:
            with self.subTest(installed=installed, tag=tag):
                result = updates.check(installed, lambda url: release(tag))
                self.assertEqual(result['status'], status)
                self.assertEqual(result['release_url'], f'{updates.RELEASES_URL}/tag/{tag}')

    def test_drafts_prereleases_and_malformed_versions_are_not_current(self):
        for data in [{}, {'tag_name': 'v0.1.1'},
                     dict(tag_name='v0.1.1', draft=True, prerelease=False),
                     dict(tag_name='v0.1.1', draft=False, prerelease=True),
                     release('v0.1.1-beta.1'), release('v0.1.1/../../other'), []]:
            with self.subTest(data=data):
                result = updates.check('0.1.1', lambda url: data)
                self.assertEqual(result['status'], 'check-failed')
                self.assertIn('error', result)

    def test_no_releases_and_rate_limits_are_distinct_from_current(self):
        for code, status in [(404, 'no-release'), (403, 'check-failed'),
                             (429, 'check-failed'), (500, 'check-failed')]:
            def fetch(url):
                raise urllib.error.HTTPError(url, code, 'error', {}, io.BytesIO())
            self.assertEqual(updates.check('0.1.1', fetch)['status'], status)

    def test_offline_check_is_not_success_and_does_not_need_hardware(self):
        def offline(url): raise OSError('offline')
        result = updates.check('0.1.1', offline)
        self.assertEqual(result['status'], 'check-failed')
        self.assertIn('offline', result['error'])

    def test_only_public_release_endpoint_and_constructed_links_are_used(self):
        urls = []
        def fetch(url):
            urls.append(url)
            return release(html_url='file:///untrusted', assets=[{'url': 'https://example.com/code'}])
        result = updates.check('0.1.0', fetch)
        self.assertEqual(urls, [updates.LATEST_URL])
        self.assertEqual(result['release_url'], f'{updates.RELEASES_URL}/tag/v0.1.1')

    def test_installed_version_comes_from_this_installation_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'manifest.json').write_text(json.dumps({'version': '0.1.1', 'id': 'example.legacy'}))
            self.assertEqual(updates.installed(root),
                             {'version': '0.1.1', 'git_managed': False, 'id': 'example.legacy'})
            (root/'.git').write_text('gitdir: somewhere')
            self.assertTrue(updates.installed(root)['git_managed'])
            (root/'manifest.json').write_text('invalid')
            self.assertIsNone(updates.installed(root)['version'])

    def test_response_limits_redirect_validation_and_no_authentication(self):
        class Response:
            url = updates.LATEST_URL
            payload = json.dumps(release()).encode()
            def read(self, limit): return self.payload[:limit]
            def __enter__(self): return self
            def __exit__(self, *args): pass
        response = Response()
        with patch.object(updates.urllib.request, 'urlopen', return_value=response) as opened:
            self.assertEqual(updates.get_release(updates.LATEST_URL)['tag_name'], 'v0.1.1')
            req = opened.call_args.args[0]
            self.assertFalse(any(key.lower() == 'authorization' for key, _ in req.header_items()))
            self.assertEqual(req.full_url, updates.LATEST_URL)
            response.url = 'https://example.com/release'
            with self.assertRaises(ValueError): updates.get_release(updates.LATEST_URL)
            response.url = updates.LATEST_URL
            response.payload = b'x' * 1_000_001
            with self.assertRaises(ValueError): updates.get_release(updates.LATEST_URL)


if __name__ == '__main__':
    unittest.main()
