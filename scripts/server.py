#!/usr/bin/env python3
"""Local academic figure studio. Originals remain immutable; crop/scale are scene metadata."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import argparse, base64, io, json, os, re, subprocess, tempfile, uuid
from urllib.parse import urlparse
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFont
from tiff_calibration import extract_calibration

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / '.sem-data'
FONT = Path(os.environ.get('FIGURE_FONT_PATH', str(Path.home() / 'Library/Fonts/SourceHanSansCN-Regular.otf')))
TESSERACT = os.environ.get('FIGURE_TESSERACT', 'tesseract')
MAX_BYTES = 100 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 80_000_000

def detect_footer(image):
    """Find an abrupt transition to a mostly solid black/white bottom banner.
    No strong transition -> retain full image. Never infer dimensions here.
    """
    gray = np.asarray(image.convert('L').resize((min(image.width, 900), image.height)))
    extreme = np.maximum((gray < 28).mean(axis=1), (gray > 235).mean(axis=1))
    candidates = []
    for y in range(int(image.height * .60), image.height - max(12, int(image.height * .025))):
        before = extreme[max(0,y-12):y].mean()
        after = extreme[y:min(image.height,y+24)].mean()
        tail = extreme[y:].mean()
        jump = after - before
        if jump > .28 and after > .70 and tail > .68:
            candidates.append((jump + .3*tail, y))
    if not candidates:
        return {'y': image.height, 'confidence': 0, 'reason': '未发现明确的信息栏边界，请检查原图'}
    score, y = max(candidates)
    # Transition averaging can displace the maximum: locate the first solid row nearby.
    for k in range(max(int(image.height*.60), y-4), min(image.height,y+5)):
        if extreme[k] > .85 and extreme[max(0,k-3):k].mean() < .70:
            y = k; break
    return {'y': int(y), 'confidence': round(min(.98, score),2), 'reason': '检测到高对比度底部信息栏，请核对裁切线'}

def scale_candidate(image, footer_y):
    """OCR a physical-length label and match a nearby horizontal bar. Suggest only."""
    if footer_y >= image.height:
        return None
    y0 = max(0,footer_y-10)
    strip = image.crop((0,y0,image.width,image.height)).convert('RGB')
    try:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'ocr.png'; strip.resize((strip.width*2,strip.height*2)).save(path)
            result = subprocess.run([TESSERACT,str(path),'stdout','--psm','11','tsv'], capture_output=True,text=True,timeout=15)
        words=[]
        for line in result.stdout.splitlines()[1:]:
            cols=line.split('\t')
            if len(cols)==12 and cols[11].strip():
                words.append({'text':cols[11], 'x':int(cols[6])/2,'y':int(cols[7])/2+y0,'w':int(cols[8])/2,'h':int(cols[9])/2})
        # Only join spatial neighbors; unrelated metadata must not become a scale label.
        for i,w in enumerate(words):
            text=w['text']
            if i+1<len(words):
                n=words[i+1]
                if abs(n['y']-w['y'])<max(w['h'],n['h']) and 0<=n['x']-(w['x']+w['w'])<80:
                    text+=' '+n['text']
            match=re.fullmatch(r'\s*(\d+(?:[.,]\d+)?)\s*(nm|[uµμ]m|mm)\s*',text,re.I)
            if not match: continue
            value=float(match[1].replace(',','.')); unit=match[2].lower(); factor=1 if unit=='nm' else 1e6 if unit=='mm' else 1000
            a=np.asarray(strip.convert('L')); lines=[]
            for yy,row in enumerate(a):
                for mask in (row>210,row<40):
                    changes=np.diff(np.pad(mask.astype(int),(1,1)))
                    for x1,x2 in zip(np.where(changes==1)[0],np.where(changes==-1)[0]):
                        length=int(x2-x1)
                        if max(20,image.width*.025)<length<image.width*.65:
                            dist=abs((x1+x2)/2-(w['x']+w['w']/2))+2*abs(yy+y0-w['y'])
                            lines.append((dist,int(x1),int(x2),int(yy+y0)))
            if lines:
                _,x1,x2,y=min(lines)
                return {'value':value,'unit':'nm' if factor==1 else 'mm' if factor==1e6 else 'µm', 'pixels':x2-x1,'nmPerPx':value*factor/(x2-x1),'points':[[x1,y],[x2,y]], 'confirmed':False}
    except (FileNotFoundError,PermissionError,subprocess.TimeoutExpired,ValueError):
        pass
    return None

def save_image(raw,name):
    if len(raw)>MAX_BYTES: raise ValueError('单张图片不能超过 100 MB')
    image=Image.open(io.BytesIO(raw))
    if image.width*image.height>80_000_000: raise ValueError('图片不能超过 8000 万像素')
    calibration=extract_calibration(image)
    image=ImageOps.exif_transpose(image)
    # Preserve raw original bytes. Display TIFF high bit depth with a documented linear mapping.
    note=''
    if image.mode in ('I;16','I;16B','I','F'):
        a=np.asarray(image,dtype=float); lo=float(np.nanmin(a)); hi=float(np.nanmax(a))
        image=Image.fromarray(np.uint8(np.clip((a-lo)/max(hi-lo,1)*255,0,255)))
        note=f'高位深图像以全局线性映射显示（{lo:g}–{hi:g} → 0–255）；原始文件保留。'
    image=image.convert('RGB')
    key=uuid.uuid4().hex; folder=DATA/key; folder.mkdir(parents=True)
    (folder/'original').write_bytes(raw); image.save(folder/'image.png')
    footer=detect_footer(image)
    result={'id':key,'name':Path(name).name,'width':image.width,'height':image.height,'url':f'/media/{key}/image.png','footer':footer,'scaleCandidate':scale_candidate(image,footer['y']) if calibration['status'] != 'ready' else None,'metadataCalibration':calibration,'note':note}
    (folder/'meta.json').write_text(json.dumps(result,ensure_ascii=False))
    return result

def demo_images():
    # Explicitly synthetic fixtures for interaction demonstration, never scientific evidence.
    results=[]
    for seed in range(4):
        rng=np.random.default_rng(seed+45); w,h=900,670
        small=Image.fromarray(rng.integers(20,210,(60,90),dtype=np.uint8)).resize((w,600),Image.Resampling.BICUBIC)
        arr=np.asarray(small).astype(float)+rng.normal(0,8,(600,w))
        im=Image.new('RGB',(w,h)); im.paste(Image.fromarray(np.uint8(np.clip(arr,0,255))).convert('RGB'),(0,0))
        d=ImageDraw.Draw(im); f=ImageFont.truetype(str(FONT),18) if FONT.exists() else ImageFont.load_default()
        d.text((20,15),'SYNTHETIC DEMO / 非实验图像',font=f,fill='white')
        d.text((20,625),'DEMO IMAGE     5.0 kV     WD 8.0 mm',font=f,fill='white')
        d.rectangle((650,618,829,622),fill='white'); d.text((710,636),'2 µm',font=f,fill='white')
        b=io.BytesIO();im.save(b,format='PNG'); item=save_image(b.getvalue(),f'演示纹理 {seed+1}（非实验数据）.png')
        item['demo']=True;item['footer']={'y':600,'confidence':1,'reason':'演示图片的已知边界'}
        item['scaleCandidate']={'value':2,'unit':'µm','pixels':180,'nmPerPx':2000/180,'points':[[650,620],[830,620]],'confirmed':False}
        results.append(item)
    return results

def prepare_scene(payload):
    scene=payload['scene']
    if not isinstance(scene,list) or len(scene)>2000: raise ValueError('无效画布')
    for el in scene:
        if el['type']=='image':
            key=el['sourceId']
            if not re.fullmatch('[a-f0-9]{32}',key): raise ValueError('无效图片编号')
            im=Image.open(DATA/key/'image.png')
            x,y,w,h=el['crop']
            if not all(np.isfinite(v) for v in (x,y,w,h)) or w<=0 or h<=0 or x<0 or y<0 or x+w>im.width+.01 or y+h>im.height+.01: raise ValueError('选区超出原图')
            out=io.BytesIO(); im.crop((round(x),round(y),round(x+w),round(y+h))).save(out,format='PNG')
            el['data']=base64.b64encode(out.getvalue()).decode()
    return payload

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def reply(self,data,kind='application/json',status=200):
        if not isinstance(data,bytes): data=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)))
        self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/health': return self.reply({'ok':True,'font':FONT.exists(),'name':'Academic Figure Studio','version':'0.4.2'})
        if path=='/font.otf': file=FONT; kind='font/otf'
        elif re.fullmatch(r'/media/[a-f0-9]{32}/image.png',path): file=DATA/path.split('/')[2]/'image.png';kind='image/png'
        else:
            file=(ROOT/'web'/('index.html' if path=='/' else path.lstrip('/'))).resolve()
            if not file.is_relative_to(ROOT/'web'): return self.reply({'error':'Not found'},status=404)
            kind={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml'}.get(file.suffix,'application/octet-stream')
        if not file.is_file(): return self.reply({'error':'Not found'},status=404)
        self.reply(file.read_bytes(),kind)
    def do_POST(self):
        # A local editor should not accept cross-origin writes from unrelated websites.
        origin=self.headers.get('Origin');host=self.headers.get('Host')
        if origin and origin!=f'http://{host}': return self.reply({'error':'不允许跨站请求'},status=403)
        try:
            length=int(self.headers.get('Content-Length',0))
            if length<=0 or length>150*1024*1024: raise ValueError('请求大小超出限制')
            p=json.loads(self.rfile.read(length));path=urlparse(self.path).path
            if path=='/api/import':
                return self.reply(save_image(base64.b64decode(p['data'],validate=True),p['name']))
            if path=='/api/demo': return self.reply(demo_images())
            if path=='/api/export':
                fmt=p['format']
                if fmt in ('png','tiff'):
                    raw=base64.b64decode(p['png'].split(',')[-1],validate=True);im=Image.open(io.BytesIO(raw));out=io.BytesIO();dpi=int(p.get('dpi',300))
                    im.save(out,format='TIFF' if fmt=='tiff' else 'PNG',**({'compression':'tiff_lzw'} if fmt=='tiff' else {}),dpi=(dpi,dpi));return self.reply(out.getvalue(),'image/tiff' if fmt=='tiff' else 'image/png')
                if fmt not in ('pdf','pptx'): raise ValueError('不支持的格式')
                if not FONT.exists(): raise ValueError('未找到思源黑体，请设置 FIGURE_FONT_PATH')
                p=prepare_scene(p);p['fontPath']=str(FONT)
                with tempfile.TemporaryDirectory() as td:
                    inp=Path(td)/'scene.json';out=Path(td)/f'figure.{fmt}';inp.write_text(json.dumps(p))
                    run=subprocess.run(['node',str(ROOT/'scripts/export.cjs'),str(inp),str(out)],capture_output=True,text=True,timeout=90,cwd=ROOT)
                    if run.returncode: raise ValueError('导出失败：'+run.stderr[-500:])
                    return self.reply(out.read_bytes(),'application/pdf' if fmt=='pdf' else 'application/vnd.openxmlformats-officedocument.presentationml.presentation')
            return self.reply({'error':'Unknown endpoint'},status=404)
        except Exception as e:
            return self.reply({'error':str(e)},status=400)

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);args=p.parse_args()
    DATA.mkdir(exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Academic Figure Studio: http://127.0.0.1:{args.port}',flush=True)
    server.serve_forever()
if __name__=='__main__': main()
