"""Authenticated per-thread notification management; no bulk account mutation."""
import json
import os
import re
import subprocess
from urllib import request,error
from nexus_release_adapters import AdapterError,NoRedirect


def api(path,method='GET',payload=None):
    # Paths are constructed by this module, never taken from API URL fields.
    if not path.startswith('/') or '://' in path: raise AdapterError('invalid_api_path')
    if os.getenv('NEXUS_GITHUB_USE_GH')=='1':
        args=[os.getenv('NEXUS_GH_EXECUTABLE','gh'),'api','--include','--method',method,path]
        if payload is not None: args+=['--input','-']
        try:
            result=subprocess.run(args,input=None if payload is None else json.dumps(payload).encode(),stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL,timeout=20,check=False)
        except subprocess.TimeoutExpired as exc: raise AdapterError('remote_timeout_outcome_unknown') from exc
        except OSError as exc: raise AdapterError('github_cli_unavailable') from exc
        raw=result.stdout.replace(b'\r\n',b'\n')
        if len(raw)>1048576: raise AdapterError('response_too_large')
        head,_,body=raw.partition(b'\n\n')
        try: status=int(head.splitlines()[0].split()[1])
        except (ValueError,IndexError): raise AdapterError('invalid_http_evidence')
        if result.returncode or status>=400:
            raise AdapterError({401:'authentication_failed',403:'permission_denied',404:'not_found'}.get(status,'remote_http_error'))
        try: return status,json.loads(body) if body.strip() else None,head.decode()
        except ValueError as exc: raise AdapterError('invalid_json') from exc
    token=os.getenv('NEXUS_GITHUB_TOKEN')
    if not token: raise AdapterError('notifications_credentials_not_configured')
    headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    data=None if payload is None else json.dumps(payload).encode()
    if data is not None: headers['Content-Type']='application/json'
    try:
        with request.build_opener(NoRedirect()).open(request.Request('https://api.github.com'+path,method=method,headers=headers,data=data),timeout=15) as response:
            raw=response.read(1048577)
            if len(raw)>1048576: raise AdapterError('response_too_large')
            return response.status,json.loads(raw) if raw else None,response.headers.get('Link','')
    except error.HTTPError as exc:
        raise AdapterError({401:'authentication_failed',403:'permission_denied',404:'not_found'}.get(exc.code,'remote_http_error')) from exc
    except (error.URLError,ValueError,TimeoutError) as exc: raise AdapterError('remote_request_failed') from exc


def _identity(user):
    if not isinstance(user,str) or not user.strip(): raise AdapterError('user_id_required')
    _,data,_=api('/user')
    if not isinstance(data,dict) or not isinstance(data.get('login'),str) or data['login'].lower()!=user.lower(): raise AdapterError('identity_mismatch')
    return data['login']


def read_notifications(user):
    login=_identity(user);seen=set();count=0
    for page in range(1,101):
        _,batch,links=api('/notifications?all=false&per_page=100&page='+str(page))
        if not isinstance(batch,list): raise AdapterError('invalid_notification_evidence')
        for item in batch:
            if not isinstance(item,dict) or not isinstance(item.get('id'),str) or item.get('unread') is not True: raise AdapterError('invalid_notification_evidence')
            if item['id'] in seen: raise AdapterError('inconsistent_snapshot')
            seen.add(item['id']);count+=1
        if 'rel="next"' not in links: break
    else: raise AdapterError('pagination_limit')
    return {'success':True,'user_id':login,'unread_count':count,'filtered_count':0,'mode':'read_only','verified':True,'snapshot_consistency':'best_effort'}


def manage_thread(user,thread_id,action,repository):
    login=_identity(user)
    if not isinstance(thread_id,str) or not re.fullmatch('[0-9]{1,20}',thread_id): raise AdapterError('invalid_thread_id')
    if not isinstance(repository,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository): raise AdapterError('repository_required')
    path='/notifications/threads/'+thread_id
    _,before,_=api(path)
    if not isinstance(before,dict) or before.get('id')!=thread_id or before.get('repository',{}).get('full_name')!=repository:
        raise AdapterError('thread_scope_mismatch')
    if action=='mark_read':
        if before.get('unread') is False: return {'success':True,'verified':True,'duplicate':True,'thread_id':thread_id,'unread':False}
        if before.get('unread') is not True: raise AdapterError('invalid_notification_evidence')
        # Mark-read has no documented inverse. Expose this limit explicitly.
        api(path,'PATCH')
        _,after,_=api(path)
        if not isinstance(after,dict) or after.get('id')!=thread_id or after.get('unread') is not False: raise AdapterError('notification_write_unconfirmed')
        return {'success':True,'verified':True,'thread_id':thread_id,'unread':False,'rollback_supported':False}
    if action not in ('subscribe','unsubscribe'): raise AdapterError('unsupported_notification_action')
    _,prior,_=api(path+'/subscription')
    if not isinstance(prior,dict) or not isinstance(prior.get('subscribed'),bool) or not isinstance(prior.get('ignored'),bool): raise AdapterError('subscription_state_unconfirmed')
    target={'subscribed':action=='subscribe','ignored':False}
    _,_,_=api(path+'/subscription','PUT',target)
    _,after,_=api(path+'/subscription')
    if not isinstance(after,dict) or any(after.get(key)!=value for key,value in target.items()): raise AdapterError('notification_write_unconfirmed')
    return {'success':True,'verified':True,'thread_id':thread_id,'user_id':login,
            'rollback':{'thread_id':thread_id,'repository':repository,'subscribed':prior['subscribed'],'ignored':prior['ignored']}}


def rollback_subscription(user,receipt):
    _identity(user)
    if not isinstance(receipt,dict) or any(not isinstance(receipt.get(key),bool) for key in ('subscribed','ignored')): raise AdapterError('invalid_rollback_receipt')
    thread_id=receipt.get('thread_id');repo=receipt.get('repository')
    if not isinstance(thread_id,str) or not re.fullmatch('[0-9]{1,20}',thread_id): raise AdapterError('invalid_thread_id')
    path='/notifications/threads/'+thread_id
    _,thread,_=api(path)
    if not isinstance(thread,dict) or thread.get('repository',{}).get('full_name')!=repo: raise AdapterError('thread_scope_mismatch')
    target={k:receipt[k] for k in ('subscribed','ignored')}
    api(path+'/subscription','PUT',target)
    _,after,_=api(path+'/subscription')
    if not isinstance(after,dict) or any(after.get(k)!=v for k,v in target.items()): raise AdapterError('notification_rollback_unconfirmed')
    return {'success':True,'verified':True,'restored':True}
