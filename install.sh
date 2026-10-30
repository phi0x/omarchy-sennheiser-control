#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == --device-access ]]; then
  exec pkexec "$project_dir/install-device-access.sh"
fi
gcc -Wall -Wextra -Werror "$project_dir/native/sdp-channel.c" -lbluetooth -o "$project_dir/native/sdp-channel"
python - "$project_dir" <<'PY'
from pathlib import Path
import json, shutil, sys, time
source = Path(sys.argv[1])
config = Path.home() / '.config/omarchy'
plugin_id = json.loads((source / 'manifest.json').read_text())['id']
plugin = config / 'plugins' / plugin_id
plugin.parent.mkdir(parents=True, exist_ok=True)
if plugin.is_symlink():
    if plugin.resolve() != source:
        raise SystemExit(f'{plugin} already points elsewhere')
    plugin.unlink()
elif plugin.exists() and plugin.resolve() != source and not (plugin / '.sennheiser-managed').exists():
    raise SystemExit(f'{plugin} already exists; not overwriting')
plugin.mkdir(exist_ok=True)
for name in ([] if plugin.resolve() == source else ['Widget.qml', 'HelpCard.qml', 'Section.qml', 'HelpData.js', 'UiRules.js', 'manifest.json', 'backend', 'native', 'licenses', 'THIRD_PARTY.md']):
    item = source / name
    if not item.exists():
        continue
    if item.is_dir():
        shutil.copytree(item, plugin / name, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
    else:
        shutil.copy2(item, plugin / name)
(plugin / '.sennheiser-managed').touch()
path = config / 'shell.json'
data = json.loads(path.read_text())
items = data['bar']['layout']['right']
if not any(x.get('id') == plugin_id for section in data['bar']['layout'].values() for x in section):
    shutil.copy2(path, path.with_name(f'shell.json.sennheiser-backup-{time.time_ns()}'))
    index = next((i for i,x in enumerate(items) if x.get('id') == 'omarchy.audio'), len(items))
    items.insert(index, {'id':plugin_id})
    temporary = path.with_suffix('.sennheiser-tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)
print(f'Installed {plugin_id} next to the audio widget.')
PY
omarchy-shell shell rescanPlugins
