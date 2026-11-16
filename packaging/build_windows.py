"""Build on Windows only; bundle the complete offline editor and export runtime."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]

def download(url, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=120) as response:
        target.write_bytes(response.read())

def main():
    if sys.platform != 'win32':
        raise SystemExit('Build this executable on a Windows x64 runner.')
    runtime=ROOT/'runtime';runtime.mkdir(exist_ok=True)
    node=Path(shutil.which('node'))
    shutil.copy2(node,runtime/'node.exe')
    node_version=subprocess.check_output([str(node),'--version'],text=True).strip()
    download(f'https://nodejs.org/dist/{node_version}/SHASUMS256.txt',runtime/'NODE-SHASUMS256.txt')
    download(f'https://raw.githubusercontent.com/nodejs/node/{node_version}/LICENSE',runtime/'NODE-LICENSE.txt')
    font=ROOT/'assets/fonts/SourceHanSansCN-Regular.otf'
    download('https://raw.githubusercontent.com/adobe-fonts/source-han-sans/2.004R/SubsetOTF/CN/SourceHanSansCN-Regular.otf',font)
    assert font.read_bytes()[:4]==b'OTTO', 'Invalid font download'
    download('https://raw.githubusercontent.com/adobe-fonts/source-han-sans/2.004R/LICENSE.txt',font.parent/'LICENSE.txt')
    version=json.loads((ROOT/'package.json').read_text())['version']
    parts=tuple(map(int,version.split('.')))+(0,)
    version_file=ROOT/'build/windows-version.txt';version_file.parent.mkdir(exist_ok=True)
    version_file.write_text(f'''VSVersionInfo(ffi=FixedFileInfo(filevers={parts},prodvers={parts},mask=0x3f,flags=0,OS=0x40004,fileType=1,subtype=0,date=(0,0)),kids=[StringFileInfo([StringTable('040904B0',[StringStruct('CompanyName','Academic Figure Studio'),StringStruct('FileDescription','Academic Figure Studio'),StringStruct('FileVersion','{version}'),StringStruct('ProductName','Academic Figure Studio'),StringStruct('ProductVersion','{version}'),StringStruct('OriginalFilename','Academic-Figure-Studio-Windows-x64.exe')])]),VarFileInfo([VarStruct('Translation',[1033,1200])])])''')
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed','--noupx','--name','Academic-Figure-Studio-Windows-x64','--version-file',str(version_file)]
    for source,destination in [('web','web'),('assets/fonts','assets/fonts'),('runtime','runtime'),('node_modules','node_modules'),('scripts/export.cjs','scripts'),('package.json','.'),('LICENSE','.')]:
        command.extend(['--add-data',f'{ROOT/source};{destination}'])
    command.append(str(ROOT/'scripts/desktop.py'))
    subprocess.run(command,cwd=ROOT,check=True)

if __name__=='__main__':main()
