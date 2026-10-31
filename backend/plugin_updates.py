"""On-demand public GitHub release metadata; never download or install code."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = 'phi0x/omarchy-sennheiser-control'
RELEASES_URL = f'https://github.com/{REPOSITORY}/releases'
LATEST_URL = f'https://api.github.com/repos/{REPOSITORY}/releases/latest'


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r'v?\d{1,5}\.\d{1,5}\.\d{1,5}', value):
        raise ValueError('Unrecognized plugin release version')
    return tuple(map(int, value.removeprefix('v').split('.')))


def installed(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent.parent
    result = {'version': None, 'git_managed': (root/'.git').exists()}
    try:
        manifest = json.loads((root/'manifest.json').read_text())
        current = manifest['version']
        version(current)
        result['version'] = current
        # A development installation may still use a legacy plugin identity.
        plugin_id = manifest.get('id', '')
        if isinstance(plugin_id, str) and re.fullmatch(r'[a-z0-9][a-z0-9._-]*', plugin_id):
            result['id'] = plugin_id
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return result


def get_release(url):
    request = urllib.request.Request(url, headers={
        'User-Agent': 'SennheiserControl',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2026-03-10',
    })
    with urllib.request.urlopen(request, timeout=10) as response:
        final = urllib.parse.urlparse(response.url)
        if final.scheme != 'https' or final.hostname != 'api.github.com':
            raise ValueError('Unexpected plugin release redirect')
        raw = response.read(1_000_001)
    if len(raw) > 1_000_000:
        raise ValueError('Plugin release response is too large')
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('Plugin release metadata is invalid')
    return data


def check(current, fetch=None):
    fetch = fetch or get_release
    result = {'installed_at_check': current, 'status': 'check-failed',
              'checked_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    try:
        release = fetch(LATEST_URL)
        if release.get('draft') is not False or release.get('prerelease') is not False:
            raise ValueError('No stable published plugin release returned')
        tag = release.get('tag_name')
        latest = version(tag)
        result['latest'] = tag.removeprefix('v')
        # Construct our own link rather than opening an API-supplied URL.
        result['release_url'] = f'{RELEASES_URL}/tag/{tag}'
        if not current:
            result['status'] = 'unknown-installed'
        else:
            local = version(current)
            result['status'] = ('update-available' if local < latest else
                                'up-to-date' if local == latest else 'newer-than-release')
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            result['status'] = 'no-release'
        elif exc.code in (403, 429):
            result['error'] = 'GitHub denied or rate-limited the check. Try again later.'
        else:
            result['error'] = f'Could not check plugin releases (HTTP {exc.code}).'
        exc.close()
    except Exception as exc:
        result['error'] = f'Could not verify plugin updates: {exc}'
    return result
