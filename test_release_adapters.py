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
            (Path(root)/'.git').mkdir()
            with patch.dict(os.environ,{'NEXUS_RELEASE_CHECKOUT':root,'NEXUS_RELEASE_REPOSITORY':'test/repo'}),patch('nexus_release_adapters.subprocess.check_output',side_effect=[b'head',b'refs',b'',b'head',b'refs',b'']),patch('nexus_release_adapters.subprocess.run',return_value=subprocess.CompletedProcess([],0,stdout='1.1.0\n')) as run:
                result=release_preview('test/repo')
                self.assertFalse(result['published']);self.assertIsNone(result['version_released'])
                self.assertEqual(result['next_version'],'1.1.0')
                self.assertIn('--noop',run.call_args.args[0]);self.assertIn('--print',run.call_args.args[0])
                self.assertNotIn('NEXUS_GITHUB_TOKEN',run.call_args.kwargs['env'])
    def test_preview_rejects_changed_state(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root)/'.git').mkdir()
            with patch.dict(os.environ,{'NEXUS_RELEASE_CHECKOUT':root,'NEXUS_RELEASE_REPOSITORY':'test/repo'}),patch('nexus_release_adapters.subprocess.check_output',side_effect=[b'head',b'refs',b'',b'changed',b'refs',b'']),patch('nexus_release_adapters.subprocess.run',return_value=subprocess.CompletedProcess([],0,stdout='1.1.0')):
                with self.assertRaisesRegex(AdapterError,'release_state_changed'): release_preview('test/repo')
    def test_preview_timeout_is_not_success(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root)/'.git').mkdir()
            with patch.dict(os.environ,{'NEXUS_RELEASE_CHECKOUT':root,'NEXUS_RELEASE_REPOSITORY':'test/repo'}),patch('nexus_release_adapters.subprocess.check_output',side_effect=[b'head',b'refs',b'']),patch('nexus_release_adapters.subprocess.run',side_effect=subprocess.TimeoutExpired('preview',90)):
                with self.assertRaisesRegex(AdapterError,'release_timeout'): release_preview('test/repo')
    def test_unapproved_repository(self):
        with patch.dict(os.environ,{'NEXUS_RELEASE_CHECKOUT':'.','NEXUS_RELEASE_REPOSITORY':'test/repo'}):
            with self.assertRaisesRegex(AdapterError,'repository_not_allowed'): release_preview('other/repo')
