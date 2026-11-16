import sys,unittest,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from server import detect_footer,save_image
from PIL import Image,ImageDraw
import numpy as np
class Processing(unittest.TestCase):
 def test_footer_both_polarities(self):
  a=np.random.default_rng(42).integers(40,215,(600,800,3),dtype=np.uint8)
  for color in ('black','white'):
   im=Image.new('RGB',(800,670),color);im.paste(Image.fromarray(a),(0,0));ImageDraw.Draw(im).text((40,625),'5 kV  WD  2 um',fill='white' if color=='black' else 'black')
   result=detect_footer(im);self.assertLessEqual(abs(result['y']-600),3);self.assertGreater(result['confidence'],.7)
 def test_no_footer_preserves_all_pixels(self):
  a=np.random.default_rng(42).integers(35,220,(670,800,3),dtype=np.uint8);self.assertEqual(detect_footer(Image.fromarray(a))['y'],670)
 def test_blank_does_not_false_crop(self):
  self.assertEqual(detect_footer(Image.new('RGB',(800,600),'black'))['y'],600)
 def test_tiff_high_bit_depth_retains_original(self):
  im=Image.fromarray(np.arange(10000,dtype=np.uint16).reshape(100,100));b=io.BytesIO();im.save(b,format='TIFF');meta=save_image(b.getvalue(),'16-bit.tif');self.assertTrue(meta['note']);self.assertEqual(meta['width'],100)

from tiff_calibration import extract_calibration
from PIL.TiffImagePlugin import ImageFileDirectory_v2, IFDRational
class TiffCalibration(unittest.TestCase):
 def metadata(self, entries, resolution=None):
  tags=ImageFileDirectory_v2()
  for key,value in entries.items():tags[key]=value
  if resolution:tags[282]=IFDRational(resolution[0]);tags[283]=IFDRational(resolution[1])
  buf=io.BytesIO();Image.new('RGB',(800,600),'gray').save(buf,format='TIFF',tiffinfo=tags);buf.seek(0)
  return extract_calibration(Image.open(buf))
 def test_fei_metres_to_nm(self):
  m=self.metadata({34682:'[Scan]\nPixelWidth=2.5e-9\nPixelHeight=2.5e-9\n'})
  self.assertEqual(m['status'],'ready');self.assertEqual(m['nmPerPx'],2.5)
 def test_zeiss_explicit_unit(self):
  m=self.metadata({34118:'AP_PIXEL_SIZE\nPixel Size = 0.015 um\n'})
  self.assertEqual(m['nmPerPx'],15)
 def test_hitachi_utf16_metadata(self):
  ini='SerialNumber=8200-16B7-03\nDataNumber=Regulus8230 0021\nSampleName=\nPixelSize=19.84375\n'
  m=self.metadata({40092:ini.encode('utf-16-le'),40093:'SU8200'.encode('utf-16-le')})
  self.assertEqual(m['status'],'ready');self.assertEqual(m['nmPerPx'],19.84375)
  self.assertEqual(m['source'],'Hitachi TIFF');self.assertEqual(m['field'],'TIFF 40092 · SemImageFile.PixelSize')
 def test_ome_default_and_explicit_units(self):
  for unit,value,expected in [('',.01,10),('PhysicalSizeXUnit="nm"',8,8)]:
   xml=f'<OME><Image><Pixels SizeX="800" SizeY="600" PhysicalSizeX="{value}" {unit}/></Image></OME>'
   self.assertEqual(self.metadata({270:xml})['nmPerPx'],expected)
 def test_imagej_resolution_needs_specimen_unit(self):
  m=self.metadata({270:'ImageJ=1.54\nunit=um\n'},resolution=(100,100))
  self.assertEqual(m['nmPerPx'],10)
 def test_print_dpi_is_not_specimen_calibration(self):
  self.assertEqual(self.metadata({296:2},resolution=(300,300))['status'],'missing')
 def test_unknown_units_or_nonpositive_values_rejected(self):
  for text in ('PixelSizeX=4 furlong','PixelSizeX=-2 nm','PixelSizeX=0 nm','PixelSizeX=nan nm','PixelWidth=1e-9'):
   self.assertEqual(self.metadata({270:text})['status'],'missing')
 def test_conflicting_metadata_is_not_automatic(self):
  m=self.metadata({34682:'[Scan]\nPixelWidth=1e-8\n',270:'PixelSizeX=30 nm'})
  self.assertEqual(m['status'],'conflict')
 def test_stale_ome_dimensions_rejected(self):
  m=self.metadata({270:'<OME><Image><Pixels SizeX="1600" SizeY="600" PhysicalSizeX="0.01"/></Image></OME>'})
  self.assertEqual(m['status'],'conflict')
 def test_orientation_uses_rotated_axis(self):
  m=self.metadata({274:6,34682:'[Scan]\nPixelWidth=2e-9\nPixelHeight=4e-9\n'})
  self.assertEqual(m['nmPerPx'],4)
 def test_rotation_missing_axis_needs_manual_calibration(self):
  m=self.metadata({274:6,34682:'[Scan]\nPixelWidth=2e-9\n'})
  self.assertEqual(m['status'],'unsupported')
 def test_import_preserves_tiff_calibration_before_conversion(self):
  tags=ImageFileDirectory_v2();tags[34682]='[Scan]\nPixelWidth=1e-8\nPixelHeight=1e-8\n';b=io.BytesIO();Image.new('RGB',(800,600),'gray').save(b,format='TIFF',tiffinfo=tags)
  m=save_image(b.getvalue(),'metadata.tif');self.assertEqual(m['metadataCalibration']['nmPerPx'],10);self.assertIsNone(m['scaleCandidate'])

if __name__=='__main__':unittest.main()
