import os
import tempfile
from pathlib import Path
import subprocess
import unittest
from unittest.mock import MagicMock,patch
from nexus_release_adapters import notifications,release_preview,AdapterError
class AdapterTests(unittest.TestCase):
    def test_notification_readback(self):
        import json
        responses=[]
        for data in [{'login':'tester'},[{'id':'1','unread':True}]]:
            r=MagicMock();r.__enter__.return_value=r;r.read.return_value=json.dumps(data).encode();r.headers={};responses.append(r)
        opener=MagicMock();opener.open.side_effect=responses
        with patch.dict(os.environ,{'NEXUS_GITHUB_TOKEN':'fake'}),patch('nexus_release_adapters.request.build_opener',return_value=opener):
            result=notifications('tester')
        self.assertEqual(result['unread_count'],1)
        self.assertEqual(result['mode'],'read_only')
        self.assertTrue(all(x.args[0].get_method()=='GET' for x in opener.open.call_args_list))
    def test_preview_never_reports_publication(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root);(path/'.git').mkdir();runner=path/'node_modules/semantic-release/bin/semantic-release.js';runner.parent.mkdir(parents=True);runner.touch()
            with patch.dict(os.environ,{'NEXUS_RELEASE_CHECKOUT':root,'NEXUS_RELEASE_REPOSITORY':'test/repo'}),patch('nexus_release_adapters.subprocess.run',return_value=subprocess.CompletedProcess([],0)) as run:
                result=release_preview('test/repo')
                self.assertFalse(result['published']);self.assertIsNone(result['version_released'])
                self.assertIn('--dry-run',run.call_args.args[0])
    def test_unapproved_repository(self):
        with patch.dict(os.environ,{'NEXUS_RELEASE_CHECKOUT':'.','NEXUS_RELEASE_REPOSITORY':'test/repo'}):
            with self.assertRaisesRegex(AdapterError,'repository_not_allowed'): release_preview('other/repo')
