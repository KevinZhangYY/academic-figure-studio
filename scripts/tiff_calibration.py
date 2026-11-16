"""Read specimen-space calibration, never infer it from ordinary print DPI.

Recognized sources: FEI SFEG/HELIOS private IFD tags (metres), Hitachi SEM
SemImageFile.PixelSize (nm), ZEISS SEM AP_PIXEL_SIZE (explicit unit), OME
Pixels (PhysicalSizeX/Y), ImageJ calibrated resolution plus specimen unit,
and explicit-unit pixel-size text.
"""
import configparser
import math
import re
import xml.etree.ElementTree as ET

NUMBER = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
UNITS = {'pm': .001, 'nm': 1, 'um': 1000, 'µm': 1000, 'μm': 1000,
         'mm': 1e6, 'cm': 1e7, 'm': 1e9, 'angstrom': .1, 'å': .1,
         'micron': 1000, 'microns': 1000, 'micrometer': 1000,
         'micrometers': 1000, 'nanometer': 1, 'nanometers': 1}

def nm(value, unit):
    unit = str(unit).strip().lower().replace('/pixel', '').replace('/px', '').strip()
    if unit not in UNITS:
        raise ValueError('unknown physical unit')
    result = float(value) * UNITS[unit]
    if not math.isfinite(result) or result <= 0 or result > 1e12:
        raise ValueError('invalid physical pixel size')
    return result

def text_value(value):
    if isinstance(value, (tuple, list)) and len(value) == 1:
        value = value[0]
    if isinstance(value, bytes):
        encoding = 'utf-16-le' if value.count(b'\x00') > len(value) // 4 else 'utf-8'
        return value.decode(encoding, errors='replace').replace('\x00', '\n')
    return value if isinstance(value, str) else ''

def extract_calibration(image):
    missing = {'status': 'missing', 'reason': '未找到可用的物理像素尺寸元数据，请根据原图机器标尺手动标定。', 'candidates': []}
    if image.format != 'TIFF' or not hasattr(image, 'tag_v2'):
        return missing
    tags = image.tag_v2
    description = text_value(tags.get(270, ''))
    candidates = []
    def add(source, x, y=None, unit='nm', field=''):
        try:
            candidates.append({'source': source, 'nmPerPxX': nm(x, unit),
                               'nmPerPxY': nm(y, unit) if y is not None else None,
                               'field': field})
        except (ValueError, TypeError, OverflowError):
            pass
    # FEI's Scan PixelWidth / PixelHeight are metres per original image pixel.
    texts = [(tag, text_value(tags.get(tag, ''))) for tag in (34680, 34682)]
    # Some exporters place the same FEI INI header in ImageDescription.
    if re.search(r'\[(?:User|System|Scan)\]', description) and re.search(r'(?im)^PixelWidth\s*=', description):
        texts.append((270, description))
    for tag, text in texts:
        if not text:
            continue
        ini = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            ini.read_string(text.strip())
            for section in ini.sections():
                if section.lower() not in ('scan', 'escan'):
                    continue
                values = ini[section]
                if 'pixelwidth' in values:
                    add('FEI / Thermo Fisher', values['pixelwidth'], values.get('pixelheight'), 'm', f'TIFF {tag} · {section}.PixelWidth')
        except configparser.Error:
            continue
    # Hitachi stores its INI metadata as UTF-16LE in private tags. PixelSize
    # is the calibrated specimen pixel size in nanometres for this vendor block.
    hitachi = text_value(tags.get(40092, ''))
    hitachi_instrument = text_value(tags.get(40093, '')).strip()
    if hitachi and 'pixelsize' in hitachi.lower() and (hitachi_instrument or re.search(r'(?im)^SerialNumber\s*=', hitachi)):
        ini = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            ini_text = hitachi.strip()
            if not re.match(r'^\s*\[', ini_text):
                ini_text = '[SemImageFile]\n' + ini_text
            ini.read_string(ini_text)
            for section in ini.sections():
                if section.lower() == 'semimagefile' and 'pixelsize' in ini[section]:
                    add('Hitachi SEM', ini[section]['pixelsize'], None, 'nm', f'TIFF {40092} · {section}.PixelSize')
        except configparser.Error:
            pass
    # ZEISS stores a key line followed by a human-readable value and unit.
    zeiss = text_value(tags.get(34118, ''))
    for text in (zeiss, description):
        match = re.search(r'(?im)^AP_(?:IMAGE_)?PIXEL_SIZE\s*\n[^\n]*?[=:]\s*('+NUMBER+r')\s*([^\s\r\n]+)', text)
        if match:
            add('ZEISS SEM', match[1], match[1], match[2], 'AP_PIXEL_SIZE')
    # OME's default physical length unit is micrometres. The first Pixels
    # belongs to the first image; reject stale dimensions after resizing.
    stale_ome = False
    if '<OME' in description or ':OME' in description:
        try:
            root = ET.fromstring(description)
            pixels = next((e for e in root.iter() if e.tag.split('}')[-1] == 'Pixels'), None)
            if pixels is not None and pixels.get('PhysicalSizeX'):
                if int(pixels.get('SizeX', image.width)) != image.width or int(pixels.get('SizeY', image.height)) != image.height:
                    stale_ome = True
                else:
                    x = nm(pixels.get('PhysicalSizeX'), pixels.get('PhysicalSizeXUnit', 'µm'))
                    y = nm(pixels.get('PhysicalSizeY'), pixels.get('PhysicalSizeYUnit', 'µm')) if pixels.get('PhysicalSizeY') else None
                    add('OME-TIFF', x, y, field='Pixels.PhysicalSizeX / PhysicalSizeY')
        except (ET.ParseError, ValueError, TypeError):
            pass
    # ImageJ uses X/YResolution in pixels per explicitly declared specimen unit.
    if re.search(r'(?im)^ImageJ\s*=', description):
        unit = re.search(r'(?im)^unit\s*=\s*([^\r\n]+)', description)
        if unit:
            try:
                xres = float(tags.get(282, 0)); yres = float(tags.get(283, 0))
                if xres > 0:
                    add('ImageJ TIFF', 1/xres, 1/yres if yres > 0 else None, unit[1], 'XResolution + ImageJ.unit')
            except (ValueError, TypeError, ZeroDivisionError):
                pass
    # Explicit units only for generic textual metadata. No implicit units for
    # unrecognized vendor fields, and no conversion of inch/cm TIFF print DPI.
    generic = description + '\n' + text_value(tags.get(50431, ''))
    matches = re.finditer(r'(?im)^\s*(PixelSizeX|PixelWidth|PixelSize|Pixel Size|PixelSizeY|PixelHeight)\s*[=:]\s*('+NUMBER+r')\s*([a-zµμÅå]+)(?:/(?:px|pixel))?\s*$', generic)
    sizes = {}
    for match in matches:
        key = match[1].lower().replace(' ', '')
        try:
            sizes[key] = nm(match[2], match[3])
        except ValueError:
            pass
    for key in ('pixelsizex', 'pixelwidth', 'pixelsize'):
        if key in sizes:
            add('TIFF 像素尺寸字段', sizes[key], sizes.get('pixelsizey', sizes.get('pixelheight', sizes.get('pixelsize'))), field=key)
    if stale_ome:
        return {'status': 'conflict', 'reason': 'OME 元数据尺寸与当前图像不一致，请用原图机器标尺重新标定。', 'candidates': candidates}
    if not candidates:
        return missing
    # Different explicit sources must agree. A discrepancy may indicate stale
    # calibration after resizing; do not silently select one source.
    orientation = int(tags.get(274, 1))
    axis = 'nmPerPxY' if orientation in (5, 6, 7, 8) else 'nmPerPxX'
    values = [c[axis] for c in candidates]
    if any(v is None for v in values):
        return {'status': 'unsupported', 'reason': '图像旋转后缺少对应轴的物理像素尺寸，请手动标定。', 'candidates': candidates}
    if any(not math.isclose(values[0], v, rel_tol=.01) for v in values[1:]):
        return {'status': 'conflict', 'reason': 'TIFF 中的像素尺寸字段相互冲突，请核对原图机器标尺并手动标定。', 'candidates': candidates}
    chosen = candidates[0]
    return {'status': 'ready', 'nmPerPx': values[0], 'source': chosen['source'],
            'field': chosen['field'], 'axis': 'Y' if axis.endswith('Y') else 'X',
            'nmPerPxX': chosen['nmPerPxX'], 'nmPerPxY': chosen['nmPerPxY'],
            'reason': '已从 TIFF 物理像素尺寸自动校准。', 'candidates': candidates}
