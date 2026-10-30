"""Build the small SDP helper in a user cache; no install hooks or root access."""
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import tempfile


def helper_path():
    source = Path(__file__).resolve().parent.parent/'native/sdp-channel.c'
    digest = hashlib.sha256(source.read_bytes()+platform.machine().encode()).hexdigest()[:20]
    cache = Path(os.environ.get('XDG_CACHE_HOME', Path.home()/'.cache'))/'sennheiser-control/native'
    cache.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = cache/f'sdp-{digest}'
    if target.is_file() and os.access(target,os.X_OK):
        return target
    fd, name = tempfile.mkstemp(prefix='.build-',dir=cache)
    os.close(fd)
    temp = Path(name)
    try:
        result = subprocess.run(['gcc','-Wall','-Wextra','-Werror',str(source),'-lbluetooth','-o',str(temp)],
                                capture_output=True,text=True,timeout=30)
        if result.returncode:
            raise OSError('Could not build Bluetooth helper. Install gcc and bluez-libs; see README.')
        temp.chmod(0o700)
        temp.replace(target)
    except FileNotFoundError:
        raise OSError('GCC is required for Bluetooth controls. Install gcc and bluez-libs; see README.') from None
    finally:
        temp.unlink(missing_ok=True)
    return target
