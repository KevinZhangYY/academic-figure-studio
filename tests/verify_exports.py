from pathlib import Path
import subprocess,zipfile
from PIL import Image
root=Path(__file__).resolve().parents[1]/'.test-output'
for fmt in ('png','tiff'):
    im=Image.open(root/f'figure.{fmt}')
    assert im.size==(2126,1535)
    assert abs(im.info['dpi'][0]-300)<.1
font=subprocess.run(['pdffonts',str(root/'figure.pdf')],text=True,capture_output=True,check=True)
assert not font.stderr,font.stderr
assert 'SourceHanSansCN' in font.stdout and 'yes' in font.stdout,font.stdout
text=subprocess.run(['pdftotext',str(root/'figure.pdf'),'-'],text=True,capture_output=True,check=True)
assert not text.stderr,text.stderr
assert '200 nm' in text.stdout and '2 µm' in text.stdout,repr(text.stdout)
with zipfile.ZipFile(root/'figure.pptx') as z:
    slide=z.read('ppt/slides/slide1.xml').decode()
    assert slide.count('<p:pic>')==5
    assert slide.count('<p:sp>')>=20
    assert 'Source Han Sans CN' in slide
print('PNG/TIFF resolution, PDF font/text, and editable PPTX checks passed.')
