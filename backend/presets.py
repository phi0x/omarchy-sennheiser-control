"""Validated named PEQ drafts stored locally; loading never writes to headphones."""
import json
import os
from pathlib import Path
from headphones import Headphones

class Presets:
    def __init__(self, path=None):
        self.path = path or Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state'))/'sennheiser-control/presets.json'
    def read(self):
        if not self.path.exists(): return {}
        if self.path.stat().st_size > 1024*1024:
            raise ValueError('Preset library is too large')
        data=json.loads(self.path.read_text())
        if not isinstance(data,dict): raise ValueError('Invalid preset library')
        return data
    def names(self): return sorted(self.read(),key=str.casefold)
    def name(self,name):
        if not isinstance(name,str) or not name.strip() or len(name.strip())>80:
            raise ValueError('Preset name must be 1–80 characters')
        return name.strip()
    def write(self,data):
        self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        temp=self.path.with_suffix('.tmp')
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        with os.fdopen(fd,'w') as f: json.dump(data,f,allow_nan=False,indent=2)
        temp.replace(self.path)
    def save(self,name,stages,pregain):
        name=self.name(name)
        Headphones.peq_commands(stages,pregain)
        data=self.read()
        data[name]=dict(stages=stages,pregain=pregain)
        self.write(data)
    def load(self,name):
        result=self.read()[self.name(name)]
        Headphones.peq_commands(result['stages'],result['pregain'])
        return result
    def delete(self,name):
        data=self.read();del data[self.name(name)];self.write(data)
