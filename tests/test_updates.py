import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import update_checker as updates

class UpdateTests(unittest.TestCase):
    def release(self, tag='v0.5.1'):
        return {'tag_name':tag,'assets':[{'name':updates.ASSET_NAME,'state':'uploaded','browser_download_url':f'{updates.RELEASES_URL}/download/{tag}/{updates.ASSET_NAME}'}]}
    def test_numeric_versions(self):
        self.assertTrue(updates.release_status('0.5.0',self.release('v0.10.0'))['available'])
        self.assertFalse(updates.release_status('0.5.0',self.release('v0.4.9'))['available'])
        self.assertFalse(updates.release_status('0.5.1',self.release())['available'])
    def test_prerelease_and_missing_or_untrusted_assets(self):
        for value in ({**self.release(),'prerelease':True},{**self.release(),'draft':True},{'tag_name':'v0.6.0','assets':[]},self.release('v0.6.0-beta')):
            self.assertFalse(updates.release_status('0.5.0',value)['available'])
        release=self.release();release['assets'][0]['browser_download_url']='https://example.com/update.exe'
        self.assertFalse(updates.release_status('0.5.0',release)['available'])
    def test_offline_failure_is_nonfatal_and_cached(self):
        updates._cache=None
        with patch.object(updates,'urlopen',side_effect=OSError('offline')) as request:
            value=updates.check_update('0.5.0')
            self.assertIn('error',value);self.assertFalse(value['available'])
            self.assertEqual(value,updates.check_update('0.5.0'));self.assertEqual(request.call_count,1)
        updates._cache=None
    def test_successful_network_check(self):
        updates._cache=None
        with patch.object(updates,'urlopen',return_value=io.BytesIO(json.dumps(self.release()).encode())):
            self.assertTrue(updates.check_update('0.5.0')['available'])
        updates._cache=None
