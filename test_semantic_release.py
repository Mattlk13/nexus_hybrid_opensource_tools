"""Real version computation; verify local/bare remote state, no publication."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from nexus_release_adapters import release_preview, AdapterError

@unittest.skipUnless(importlib.util.find_spec('semantic_release'), 'install requirements-release.txt')
class RealReleaseTests(unittest.TestCase):
    def test_conventional_versions_duplicate_and_no_mutations(self):
        with tempfile.TemporaryDirectory(prefix='nexus-release-fixture-') as temp:
            root=Path(temp); remote=root/'remote.git'; work=root/'work'
            def git(*args, cwd=None):
                return subprocess.check_output(['git',*args],cwd=cwd or work,stderr=subprocess.DEVNULL,text=True).strip()
            subprocess.run(['git','init','--bare',str(remote)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            subprocess.run(['git','clone',str(remote),str(work)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            git('checkout','-b','main');git('config','user.email','fixture@example.invalid');git('config','user.name','NEXUS fixture')
            def commit(message):
                (work/'fixture').write_text(message);git('add','.');git('commit','-m',message)
            commit('chore: initial');git('tag','v1.0.0');commit('feat: isolated feature')
            git('push','origin','main','--tags')
            # PSR identifies its VCS from the URL. No network command is run.
            git('remote','set-url','origin','https://github.com/nexus-fixture/isolated.git')
            bare_before=git('--git-dir',str(remote),'show-ref')
            with patch.dict(os.environ,{'NEXUS_RELEASE_CHECKOUT':str(work),'NEXUS_RELEASE_REPOSITORY':'nexus-fixture/isolated'}):
                first=release_preview('nexus-fixture/isolated')
                self.assertEqual(first['next_version'],'1.1.0')
                self.assertEqual(first,release_preview('nexus-fixture/isolated'))
                git('tag','v1.1.0');commit('fix: isolated correction')
                self.assertEqual(release_preview('nexus-fixture/isolated')['next_version'],'1.1.1')
                commit('feat: change interface\n\nBREAKING CHANGE: fixture interface changed')
                self.assertEqual(release_preview('nexus-fixture/isolated')['next_version'],'2.0.0')
                (work/'dirty').write_text('uncommitted')
                with self.assertRaisesRegex(AdapterError,'release_checkout_dirty'):
                    release_preview('nexus-fixture/isolated')
            self.assertEqual(git('--git-dir',str(remote),'show-ref'),bare_before)
            self.assertEqual(git('tag','--list'),'v1.0.0\nv1.1.0')
            self.assertFalse(first['published'])
