"""Read-only checks against Sennheiser's official catalog. No DFU or flashing."""
from datetime import datetime, timezone
import json
import re
import urllib.parse
import urllib.request

HOST = 'api.s-consumer-cloud.com'
ROOT = f'https://{HOST}/firmware/api/v2'
PRODUCTS = {'dongle': '700434', 'headphones': '700445'}


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{1,5}\.\d{1,5}\.\d{1,5}', value):
        raise ValueError('Unrecognized firmware version')
    return tuple(map(int, value.split('.')))


def get_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'SennheiserControl/0.1'})
    with urllib.request.urlopen(request, timeout=10) as response:
        final = urllib.parse.urlparse(response.url)
        if final.scheme != 'https' or final.hostname != HOST:
            raise ValueError('Unexpected firmware catalog redirect')
        raw = response.read(1_000_001)
    if len(raw) > 1_000_000:
        raise ValueError('Firmware catalog response is too large')
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get('success') is not True:
        raise ValueError('Firmware catalog did not return a successful response')
    return data


def check(installed, fetch=None):
    fetch = fetch or get_json
    result = {'checked_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'devices': {}}
    for key, product in PRODUCTS.items():
        item = {'installed_at_check': installed.get(key), 'status': 'unknown'}
        try:
            catalog = fetch(f'{ROOT}/availableSystemReleases/{product}?os_type=android')
            releases = catalog.get('data')
            if catalog.get('success') is not True or not isinstance(releases, list) or not releases:
                raise ValueError('Firmware release list is missing or empty')
            latest = max(releases, key=version)
            item['latest'] = latest
            current = installed.get(key)
            if not current:
                item['status'] = 'connect-device'
            else:
                a, b = version(current), version(latest)
                item['status'] = 'up-to-date' if a == b else 'update-available' if a < b else 'newer-than-catalog'
        except Exception as exc:
            item['status'] = 'check-failed'
            item['error'] = f'Could not verify firmware: {exc}'
        result['devices'][key] = item
    return result
