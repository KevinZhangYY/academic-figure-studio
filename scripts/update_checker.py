"""Read-only release checks; never download or execute updates automatically."""
import json
import re
import threading
import time
from urllib.request import Request, urlopen

REPOSITORY = 'KevinZhangYY/academic-figure-studio'
RELEASES_URL = f'https://github.com/{REPOSITORY}/releases'
ASSET_NAME = 'Academic-Figure-Studio-Windows-x64.exe'
_lock = threading.Lock()
_cache = None
_cache_time = 0

def version_tuple(value):
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', value or '')
    return tuple(map(int, match.groups())) if match else None

def release_status(current, release):
    result = {'currentVersion': current, 'available': False, 'releaseUrl': RELEASES_URL}
    latest = version_tuple(release.get('tag_name'))
    if release.get('draft') or release.get('prerelease') or not latest:
        return result
    tag = release['tag_name']
    expected = f'{RELEASES_URL}/download/{tag}/{ASSET_NAME}'
    asset = next((a for a in release.get('assets', []) if a.get('name') == ASSET_NAME and a.get('state') == 'uploaded' and a.get('browser_download_url') == expected), None)
    if not asset:
        return result
    result.update(latestVersion=tag.lstrip('v'), available=latest > version_tuple(current),
                  releaseUrl=f'{RELEASES_URL}/tag/{tag}', downloadUrl=expected)
    return result

def check_update(current):
    global _cache, _cache_time
    with _lock:
        if _cache is not None and time.monotonic() - _cache_time < 300:
            return dict(_cache)
        try:
            request = Request(f'https://api.github.com/repos/{REPOSITORY}/releases/latest',
                              headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'Academic-Figure-Studio'})
            with urlopen(request, timeout=6) as response:
                release = json.loads(response.read(2_000_000))
            result = release_status(current, release)
        except Exception:
            result = {'currentVersion': current, 'available': False, 'error': '暂时无法检查更新，请稍后重试或访问 GitHub Releases。', 'releaseUrl': RELEASES_URL}
        _cache, _cache_time = result, time.monotonic()
        return dict(result)
