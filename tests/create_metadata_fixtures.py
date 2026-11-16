from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from PIL.TiffImagePlugin import ImageFileDirectory_v2
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'.test-output';out.mkdir(exist_ok=True)
im=Image.new('RGB',(800,620),'black');rng=np.random.default_rng(55);texture=np.uint8(rng.integers(120,255,(550,800)));im.paste(Image.fromarray(texture).convert('RGB'),(0,0))
d=ImageDraw.Draw(im);font=ImageFont.truetype(str(Path.home()/'Library/Fonts/SourceHanSansCN-Regular.otf'),18)
d.rectangle((500,570,699,574),fill='white');d.text((568,587),'2 µm',fill='white',font=font);d.text((15,575),'SYNTHETIC TEST',fill='white',font=font)
tags=ImageFileDirectory_v2();tags[34682]='[Scan]\nPixelWidth=1e-8\nPixelHeight=1e-8\n'
im.save(out/'metadata.tif',tiffinfo=tags);im.save(out/'manual.tif')
