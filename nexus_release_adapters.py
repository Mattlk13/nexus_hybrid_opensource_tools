"""Read-only GitHub notifications and non-publishing semantic-release preview.

Only an operator-selected trusted checkout may execute release plugins.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib import request, error

class AdapterError(RuntimeError):
    pass

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise AdapterError('redirect_rejected')

def notifications(user):
    token=os.getenv('NEXUS_GITHUB_TOKEN')
    if not token:
        raise AdapterError('notifications_credentials_not_configured')
    def get(path):
        req=request.Request('https://api.github.com'+path, headers={
            'Authorization':'Bearer '+token, 'Accept':'application/vnd.github+json',
            'X-GitHub-Api-Version':'2022-11-28'})
        try:
            with request.build_opener(NoRedirect()).open(req,timeout=15) as res:
                raw=res.read(1048577)
                if len(raw)>1048576: raise AdapterError('response_too_large')
                return json.loads(raw), res.headers.get('Link','')
        except error.HTTPError as exc:
            raise AdapterError({401:'authentication_failed',403:'permission_denied'}.get(exc.code,'remote_http_error')) from exc
        except (error.URLError,TimeoutError,ValueError) as exc:
            raise AdapterError('remote_request_failed') from exc
    identity,_=get('/user')
    if not isinstance(identity,dict) or identity.get('login','').lower()!=user.lower():
        raise AdapterError('identity_mismatch')
    items=[]
    for page in range(1,101):
        batch,link=get('/notifications?all=false&per_page=100&page='+str(page))
        if not isinstance(batch,list) or any(not isinstance(x,dict) or not isinstance(x.get('id'),str) or x.get('unread') is not True for x in batch):
            raise AdapterError('invalid_notification_evidence')
        items.extend(batch)
        if 'rel="next"' not in link: break
    else: raise AdapterError('pagination_limit')
    ids=[x['id'] for x in items]
    if len(ids)!=len(set(ids)): raise AdapterError('inconsistent_snapshot')
    return {'success':True,'user_id':identity['login'],'unread_count':len(items),
            'filtered_count':0,'mode':'read_only','verified':True,'snapshot_consistency':'best_effort'}

def release_preview(repo):
    root=os.getenv('NEXUS_RELEASE_CHECKOUT')
    expected=os.getenv('NEXUS_RELEASE_REPOSITORY')
    if not root or not expected: raise AdapterError('semantic_release_runner_not_configured')
    if repo!=expected or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):
        raise AdapterError('repository_not_allowed')
    path=Path(root).resolve()
    if not (path/'.git').exists(): raise AdapterError('release_checkout_missing')
    # Do not inherit service tokens or load checkout Python modules.
    env={k:os.environ[k] for k in ('PATH','HOME','SystemRoot','TEMP','TMP','LANG') if k in os.environ}
    def state():
        try:
            return tuple(subprocess.check_output(['git',*args],cwd=path,env=env,stderr=subprocess.DEVNULL,timeout=15)
                         for args in (['rev-parse','HEAD'],['show-ref','--head'],['status','--porcelain=v1','--untracked-files=all']))
        except (OSError,subprocess.SubprocessError) as exc:
            raise AdapterError('release_state_unavailable') from exc
    before=state()
    if before[2].strip(): raise AdapterError('release_checkout_dirty')
    try:
        # Fixed config avoids project build/publish hooks. Only compute a version.
        with tempfile.TemporaryDirectory(prefix='nexus-release-preview-') as temp:
            config=Path(temp)/'pyproject.toml'
            config.write_text('[tool.semantic_release]\n',encoding='utf-8')
            result=subprocess.run([sys.executable,'-I','-m','semantic_release','--noop','--config',str(config),'version','--print'],
                cwd=path,env=env,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=90,check=False)
    except subprocess.TimeoutExpired as exc: raise AdapterError('release_timeout') from exc
    except OSError as exc: raise AdapterError('release_runner_failed') from exc
    if state()!=before: raise AdapterError('release_state_changed')
    if result.returncode: raise AdapterError('release_preview_failed')
    version=result.stdout.strip()
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?',version):
        raise AdapterError('release_version_unverified')
    return {'success':True,'repo':repo,'mode':'dry_run','published':False,
            'next_version':version,'version_released':None,'changelog_generated':False,
            'backend':'python-semantic-release','git_state_unchanged':True,
            'evidence':'no-op version preview; HEAD, refs and worktree readback unchanged'}
