#!/usr/bin/env python3
if __name__!='__main__':raise ImportError('Explicit launch only')
from pathlib import Path
from datetime import datetime
import os,sys,time,json,subprocess,hashlib,fcntl,traceback
P=Path(__file__).resolve().parent;R=P.parents[1]
def now():return datetime.now().astimezone().isoformat()
def status(s):(P/'status.txt').write_text(s+'\n')
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
lock=(P/'campaign.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
previous=R/'result/inherit-20261006'
status('waiting_for_mixV_fixed50_campaign_validated_completion')
while not (previous/'result.json').exists():
 state=subprocess.check_output(['systemctl','--user','show','icat-inherit-20261006','-p','ActiveState','--value'],text=True).strip()
 if state not in ('active','activating'):
  status('blocked_previous_ended_without_result');raise SystemExit(1)
 time.sleep(10)
prior=json.loads((previous/'result.json').read_text())
if prior.get('status')!='validated_saved_evidence' or prior.get('exit_code')!=0:
 status('blocked_previous_failed');raise SystemExit(1)
status('waiting_for_exclusive_virtual_device_lock')
shared=(R/'result/mix-20260911/device.lock').open('w');fcntl.flock(shared,fcntl.LOCK_EX)
meta=json.loads((P/'metadata.json').read_text());rc=1;issues=[];proc=None
try:
 for f,h in meta['execution_sha256'].items():assert digest(P/f)==h,'Changed execution input '+f
 assert (R/'script/icat2-mixX.sh').read_bytes()==(P/'execution-entrypoint.sh').read_bytes(),'entrypoint changed'
 for f,h in meta['workload_sha256'].items():assert digest(R/f)==h,'Changed workload '+f
 for policy,m in meta['modules'].items():
  assert digest(Path(m['path']))==m['sha256'],'Changed module '+policy
  assert subprocess.check_output(['modinfo','-F','vermagic',m['path']],text=True).split()[0]==os.uname().release,'Kernel/module mismatch'
  for base in [P,P/'fitcheck']:assert not (base/f'mixX-{policy}-rep1').exists(),'Refuse overwrite'
 assert not Path('/sys/module/nvmev').exists(),'Device module occupied'
 assert subprocess.run(['mountpoint','-q',str(R/'mnt')]).returncode!=0,'Mount occupied'
 meta['started_at']=now();(P/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
 env=os.environ.copy()
 for k in ['SMOKE','PH_SECS','MULT','VM_FILES','VM_RUN','VM_CHUNKS','YCSB_SECS','PRE_FIO','ICAT_ROOT','MNT_DIR','MIXV_FIO_GB','MIXV_RECORDS']:env.pop(k,None)
 env.update(DEV='/dev/nvme1n1',ICAT_ROOT=str(R),MNT_DIR=str(R/'mnt'),MIX_BASE=str(P),MIX_JOURNAL=str(P/'journal.md'),BASH_ENV=str(P/'safety-env.sh'),MIXX_LOCK_HELD='1')
 with (P/'pipeline.console.txt').open('x') as output:
  proc=subprocess.Popen(['bash','script/icat2-mixX.sh'],cwd=R,env=env,stdout=output,stderr=subprocess.STDOUT)
  (P/'pipeline.pid').write_text(str(proc.pid)+'\n')
  while proc.poll() is None:
   stage=(P/'current-stage.txt').read_text().strip() if (P/'current-stage.txt').exists() else 'preparation'
   policy=stage.split('-')[0]
   raw=(P/'fitcheck' if stage.endswith('fitcheck') else P)/f'mixX-{policy}-rep1'
   begun=[slot for slot in meta['phase_slots'] if (raw/f'phase-{slot}-start.time').exists()]
   status('running_'+stage+'_'+(begun[-1] if begun else 'preparation'));time.sleep(2)
  rc=proc.wait()
 if rc:issues.append('entrypoint exited '+str(rc)+'; inspect pipeline console and stage logs')
 for policy in ['fixed50','fixed37']:
  for stage in ['fitcheck','long']:
   f=P/f'{policy}-{stage}-result.json'
   if not f.exists() or json.loads(f.read_text()).get('status')!='validated_saved_evidence':issues.append(policy+' '+stage+' not validated')
except Exception:
 issues.append(traceback.format_exc());(P/'launcher-error.txt').write_text(issues[-1])
result=dict(run_id=P.name,exit_code=rc if rc else (1 if issues else 0),status='failed_or_incomplete_preserved' if issues else 'validated_saved_evidence',issues=issues,finished_at=now(),source_commit=meta['source_commit'],raw_path=str(P))
(P/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(P/'exit-code.txt').write_text(str(result['exit_code'])+'\n');status(result['status'])
for f in [P/'journal.md',P/'report.md',R/'EXPERIMENT_LOG.md']:
 with f.open('a') as out:out.write('\n- mixX campaign FINISHED '+json.dumps(result,ensure_ascii=False)+'\n')
pub=subprocess.call(['python3',str(P/'publish-results.py')],cwd=R);(P/'publish.exit').write_text(str(pub)+'\n')
subprocess.run(['notify-send','iCAT mixX',result['status']],check=False)
raise SystemExit(result['exit_code'] or pub)
