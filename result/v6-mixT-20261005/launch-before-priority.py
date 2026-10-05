#!/usr/bin/env python3
"""Wait for earlier authorized queue, then execute the requested v6 pipeline."""
if __name__!='__main__':raise ImportError('Explicit launch only')
from pathlib import Path
from datetime import datetime
import os,sys,json,subprocess,fcntl,time,hashlib,shutil,csv,re
P=Path(__file__).resolve().parent;R=P.parents[1]
def now():return datetime.now().astimezone().isoformat()
def status(s):(P/'status.txt').write_text(s+'\n')
def journal(s):
 for f in [P/'journal.md',R/'EXPERIMENT_LOG.md']:
  with f.open('a') as out:out.write('\n- '+now()+' '+P.name+' '+s+'\n')
def notify(message):
 try:subprocess.run(['notify-send','iCAT v6 실험',message],timeout=10,check=False,capture_output=True)
 except Exception:pass
campaign_lock=(P/'campaign.lock').open('w');fcntl.flock(campaign_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
meta=json.loads((P/'metadata.json').read_text());rc=1;error=None;started=None
try:
 previous=R/'result'/meta['wait_for']
 while not (previous/'result.json').exists():
  status('waiting_for_mixU_fixed50_completion;v6_build_and_smoke_NOT_started')
  state=subprocess.check_output(['systemctl','--user','show','icat-'+meta['wait_for'],'-p','ActiveState','--value'],text=True).strip()
  if state not in ('active','activating'):raise RuntimeError('Earlier queue ended without validated result; v6 not started')
  time.sleep(10)
 prior=json.loads((previous/'result.json').read_text())
 assert prior.get('status')=='validated_saved_evidence' and prior.get('exit_code')==0,'Earlier queue validation failed; no v6 device initialization'
 shared=(R/'result/mix-20260911/device.lock').open('w');fcntl.flock(shared,fcntl.LOCK_EX)
 assert not Path('/sys/module/nvmev').exists(),'Virtual module occupied'
 assert subprocess.run(['mountpoint','-q',str(R/'mnt')]).returncode!=0,'Mount occupied'
 assert hashlib.sha256((R/'script/icat2-v6-mixT.sh').read_bytes()).hexdigest()==meta['entrypoint_sha256'],'Entrypoint changed while queued'
 assert hashlib.sha256((P/'execution-mix.sh').read_bytes()).hexdigest()==meta['execution_script_sha256'],'Measurement snapshot changed'
 for f,h in json.loads((P/'source-manifest.json').read_text()).items():
  assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h,'v6 source changed: '+f
 for f,h in meta['workload_sha256'].items():
  assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h,'workload changed: '+f
 # Preserve any externally created v6 build before the authorized rebuild.
 for f in ['buildoutput/nvmev-online-v6.ko','buildoutput/build-online-v6.log']:
  if (R/f).exists():shutil.copy2(R/f,P/('previous-'+Path(f).name))
 started=now();meta['pipeline_started_at']=started;(P/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
 status('building_v6');journal('START authorized v6 build -> smoke gate -> long pipeline')
 env=os.environ.copy()
 for name in ['SMOKE','PH_SECS','VM_RUN','VM_CHUNKS','VM_FILES','MULT','YCSB_SECS']:env.pop(name,None)
 env.update(CAMPAIGN_DIR=str(P),MIX_BASE=str(P),MIX_JOURNAL=str(P/'journal.md'),BASH_ENV=str(P/'safety-env.sh'),DEV='/dev/nvme1n1')
 with (P/'pipeline.console.txt').open('w') as console:
  proc=subprocess.Popen(['bash','script/icat2-v6-mixT.sh'],cwd=R,env=env,stdout=console,stderr=subprocess.STDOUT)
  (P/'pipeline.pid').write_text(str(proc.pid)+'\n')
  while proc.poll() is None:
   stage=(P/'current-stage.txt').read_text().strip() if (P/'current-stage.txt').exists() else 'build'
   if stage!='build':
    d=P/('mixT-onlinev6-rep1-smoke' if stage=='smoke' else 'mixT-onlinev6-rep1')
    slots=[x for x in 'ABCDEFGHI' if (d/f'phase-{x}-start.time').exists()]
    status('running_'+stage+'_'+(slots[-1] if slots else 'preparation'))
   time.sleep(2)
  rc=proc.wait()
except Exception as e:error=str(e)
finished=now()
long=json.loads((P/'long-result.json').read_text()) if (P/'long-result.json').exists() else None
ok=rc==0 and long and long.get('status')=='validated_saved_evidence'
result={'run_id':P.name,'status':'validated_saved_evidence' if ok else 'stopped_failure_preserved','exit_code':rc,'started_at':started,'finished_at':finished,'error':error,'smoke_result':str(P/'smoke-result.json'),'long_result':str(P/'long-result.json'),'short_failure_blocks_long':True}
if ok:result['waf']=long['waf']
(P/'result.json').write_text(json.dumps(result,indent=2)+'\n');(P/'exit-code.txt').write_text(str(rc if rc else (0 if ok else 1))+'\n');status(result['status']);journal('FINISHED '+json.dumps(result))
# Preserve build failure evidence even if the build hook never ran.
f=R/'buildoutput/build-online-v6.log'
if started and f.exists():shutil.copy2(f,P/'build-online-v6.log')
if not ok:notify('v6 실행이 중단됐습니다. 짧은 시험 미통과 시 10시간 실행은 시작하지 않았습니다. '+str(P/'status.txt'))
publish=subprocess.call(['python3',str(P/'publish-results.py')],cwd=R)
(P/'publish.exit').write_text(str(publish)+'\n')
if publish:notify('v6 결과 push 실패. 로컬 로그는 보존되어 있습니다.')
raise SystemExit(rc if rc else (0 if ok and publish==0 else 1))
