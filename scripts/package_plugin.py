#!/usr/bin/env python3
"""Build a local marketplace and ZIP without importing private project data."""
from pathlib import Path
import json,shutil,zipfile
root=Path(__file__).resolve().parents[1]
market=root/'dist'/'academic-figure-marketplace'
plugin=market/'plugins'/'academic-figure-studio'
plugin.mkdir(parents=True,exist_ok=True)
for name in ('.codex-plugin','skills','assets','web','scripts','node_modules'):
    target=plugin/name
    if target.exists():shutil.rmtree(target)
    shutil.copytree(root/name,target,ignore=shutil.ignore_patterns('__pycache__'))
for name in ('package.json','package-lock.json','requirements.txt','README.md','LICENSE'):
    shutil.copy2(root/name,plugin/name)
manifest=market/'.agents'/'plugins'/'marketplace.json';manifest.parent.mkdir(parents=True,exist_ok=True)
manifest.write_text(json.dumps({'name':'academic-figure-local','plugins':[{'name':'academic-figure-studio','source':{'source':'local','path':'./plugins/academic-figure-studio'},'policy':{'installation':'AVAILABLE','authentication':'ON_USE'},'category':'Productivity'}]},indent=2))
archive=root/'dist'/'academic-figure-studio.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for file in market.rglob('*'):
        if file.is_file():z.write(file,file.relative_to(market.parent))
print(archive)
