"""Exercise the built EXE with no Python or Node on its subprocess PATH."""
import base64
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen
from zipfile import ZipFile
from PIL import Image, TiffImagePlugin

ROOT=Path(__file__).resolve().parents[1]
def main():
    with tempfile.TemporaryDirectory() as td:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        env={**os.environ,'FIGURE_DATA_DIR':td,'PATH':os.path.join(os.environ['SystemRoot'],'System32')}
        env.pop('FIGURE_FONT_PATH',None)
        proc=subprocess.Popen([str(ROOT/'dist/Academic-Figure-Studio-Windows-x64.exe'),'--headless','--port',str(port)],env=env)
        base=f'http://127.0.0.1:{port}'
        def get(path):
            with urlopen(base+path,timeout=10) as r:return r.read()
        def post(path,payload):
            request=Request(base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
            with urlopen(request,timeout=90) as r:return r.read()
        try:
            for _ in range(120):
                if proc.poll() is not None:raise RuntimeError('Packaged EXE exited before startup')
                try:health=json.loads(get('/api/health'));break
                except OSError:time.sleep(1)
            else:raise RuntimeError('EXE startup timeout')
            assert health['desktop'] and health['font']
            assert health['version']==json.loads((ROOT/'package.json').read_text())['version']
            assert b'checkUpdates' in get('/')
            assert get('/font.otf')[:4]==b'OTTO'
            # Explicit synthetic TIFF fixture with known calibration, never user data.
            tags=TiffImagePlugin.ImageFileDirectory_v2();tags[34682]='[Scan]\nPixelWidth=2.5e-9\nPixelHeight=2.5e-9\n'
            buf=io.BytesIO();Image.new('RGB',(80,60),'gray').save(buf,format='TIFF',tiffinfo=tags)
            raw=buf.getvalue()
            imported=json.loads(post('/api/import',{'name':'synthetic-smoke.tif','data':base64.b64encode(raw).decode()}))
            assert imported['metadataCalibration']['nmPerPx']==2.5
            assert (Path(td)/imported['id']/'original').read_bytes()==raw
            scene=[{'type':'image','sourceId':imported['id'],'crop':[0,0,80,60],'x':0,'y':0,'w':400,'h':300},
                   {'type':'text','text':'形貌分析 100 nm','x':20,'y':320,'size':20,'color':'#000000','align':'left','outline':'#ffffff','outlineWidth':1.1}]
            for fmt in ('pdf','pptx'):
                result=post('/api/export',{'format':fmt,'widthMm':180,'heightMm':130,'width':1000,'height':722,'scene':scene})
                if fmt=='pdf':assert result.startswith(b'%PDF') and len(result)>1_000_000
                else:
                    with ZipFile(io.BytesIO(result)) as z:assert 'ppt/slides/slide1.xml' in z.namelist()
            png=get(imported['url'])
            for fmt in ('png','tiff'):
                result=post('/api/export',{'format':fmt,'dpi':300,'png':'data:image/png;base64,'+base64.b64encode(png).decode()})
                with Image.open(io.BytesIO(result)) as image:assert image.size==(80,60)
            print('PASS: packaged EXE starts; bundled font, TIFF calibration, immutable original, PNG/TIFF/PDF/PPTX exports work without installed Python/Node.')
        finally:
            proc.terminate();proc.wait(timeout=20)
if __name__=='__main__':main()
