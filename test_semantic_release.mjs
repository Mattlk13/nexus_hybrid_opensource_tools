import {pathToFileURL} from 'node:url';
import semanticRelease from 'semantic-release';
import {mkdtempSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
const root=mkdtempSync(join(tmpdir(),'nexus-release-'));
const remote=join(root,'remote.git'),work=join(root,'work');
const git=(args,cwd)=>execFileSync('git',args,{cwd,encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();
try {
 git(['init','--bare',remote]);git(['clone',remote,work]);
 git(['checkout','-b','main'],work);git(['config','user.email','fixture@example.invalid'],work);git(['config','user.name','NEXUS fixture'],work);
 writeFileSync(join(work,'README'),'fixture');git(['add','.'],work);git(['commit','-m','chore: initial'],work);git(['tag','v1.0.0'],work);
 writeFileSync(join(work,'feature'),'feature');git(['add','.'],work);git(['commit','-m','feat: isolated release preview'],work);git(['push','origin','main','--tags'],work);git(['--git-dir',remote,'symbolic-ref','HEAD','refs/heads/main']);
 const result=await semanticRelease({branches:['main'],repositoryUrl:pathToFileURL(remote).href,dryRun:true,ci:false,
   extends:[],plugins:['@semantic-release/commit-analyzer','@semantic-release/release-notes-generator']},
   {cwd:work,env:{...process.env,GITHUB_TOKEN:'',GH_TOKEN:'',NPM_TOKEN:''}});
 assert.equal(result.nextRelease.version,'1.1.0');
 assert.equal(git(['tag','--list'],work),'v1.0.0');
 assert.equal(git(['--git-dir',remote,'tag','--list']),'v1.0.0');
 console.log('PASS: semantic-release computed 1.1.0; local and remote tags unchanged');
} finally {rmSync(root,{recursive:true,force:true});}
