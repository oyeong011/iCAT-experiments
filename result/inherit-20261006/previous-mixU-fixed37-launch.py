#!/usr/bin/env python3
if __name__ != '__main__':
 raise ImportError('Explicit experiment launch only')
import os,csv,json,re,time,subprocess,fcntl
from pathlib import Path
from datetime import datetime
P=Path(__file__).resolve().parent;ROOT=P.parents[1];D=P/'mixU-fixed37-rep1'
lock=(P/'campaign.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
previous=ROOT/'result/mixU-onlinev4-after-v6-20261005'
while not (previous/'result.json').exists():
 (P/'status.txt').write_text('waiting_for_onlinev4_validated_completion\n')
 state=subprocess.check_output(['systemctl','--user','show','icat-mixU-onlinev4-after-v6-20261005','-p','ActiveState','--value'],text=True).strip()
 if state not in ('active','activating'):
  (P/'status.txt').write_text('blocked_previous_ended_without_result\n');raise SystemExit(1)
 time.sleep(10)
prior=json.loads((previous/'result.json').read_text())
if prior.get('status')!='validated_saved_evidence' or prior.get('exit_code')!=0:
 (P/'status.txt').write_text('blocked_previous_failed\n');raise SystemExit(1)
shared=(ROOT/'result/mix-20260911/device.lock').open('w');fcntl.flock(shared,fcntl.LOCK_EX)
assert __import__('hashlib').sha256((P/'execution-script.sh').read_bytes()).hexdigest()==json.loads((P/'metadata.json').read_text())['execution_script_sha256'],'Latest script changed; inspect before launch'
assert not D.exists(),'Refusing overwrite'
assert not Path('/sys/module/nvmev').exists(),'Virtual module occupied; no reset'
assert subprocess.run(['mountpoint','-q',str(ROOT/'mnt')]).returncode!=0,'Mount occupied'
meta=json.loads((P/'metadata.json').read_text());env=os.environ.copy()
for k in ['SMOKE','VM_FILES','MULT','VM_RUN','VM_CHUNKS','YCSB_SECS']:env.pop(k,None)
env.update(PH_SECS='4500',DEV='/dev/nvme1n1',MIX_BASE=str(P),MIX_JOURNAL=str(P/'journal.md'),BASH_ENV=str(P/'safety-env.sh'))
assert __import__('hashlib').sha256(Path(meta['module_path']).read_bytes()).hexdigest()==meta['module_sha256'],'Module changed'
for filename,digest in meta['workload_sha256'].items():
 assert __import__('hashlib').sha256((ROOT/filename).read_bytes()).hexdigest()==digest,'Workload changed: '+filename
(P/'status.txt').write_text('running_preparation\n')
start=datetime.now().astimezone().isoformat();meta['started_at']=start;(P/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
console=(P/'mixU-fixed37.console.txt').open('w')
proc=subprocess.Popen(['bash',str(P/'execution-script.sh'),'mixU','fixed37','1'],cwd=ROOT,env=env,stdout=console,stderr=subprocess.STDOUT)
(P/'runner.pid').write_text(str(proc.pid)+'\n')
ledger=(P/'waf-series.csv').open('w',newline='',buffering=1)
fields=['unix_timestamp','iso_time','elapsed_measured_seconds','phase','epoch','active','host_bytes','host_pages','gc_pages','cumulative_waf','sample_status','source']
w=csv.DictWriter(ledger,fieldnames=fields);w.writeheader();offset=0;count=0

PHASES=dict(zip('ABCDEFGH',meta['phase_order']))
def phase(ts=None):
 observed=[]
 for slot,name in PHASES.items():
  f=D/f'phase-{slot}-start.time'
  if f.exists():
   start_ts=datetime.fromisoformat(f.read_text().strip()).timestamp()
   if ts is None or start_ts<=ts:observed.append((start_ts,slot+'_'+name))
 return max(observed)[1] if observed else 'preparation'

def consume():
 global offset,count
 f=D/'control-series.txt'
 if not f.exists():return
 with f.open() as raw:
  raw.seek(offset);lines=raw.readlines();offset=raw.tell()
 for line in lines:
  ts=line.split()[0] if line.split() else ''
  if not ts.isdigit():continue
  k={a:int(b) for a,b in re.findall(r'\b(epoch|active|host_bytes|host_pages|gc_pages)=(\d+)',line)}
  t0=D/'phase-A-start.time';elapsed=''
  if t0.exists():elapsed=int(ts)-datetime.fromisoformat(t0.read_text().strip()).timestamp()
  good=k.get('active')==1 and k.get('host_pages',0)>0
  row=dict(unix_timestamp=int(ts),iso_time=datetime.fromtimestamp(int(ts)).astimezone().isoformat(),elapsed_measured_seconds=elapsed,phase=phase(int(ts)),cumulative_waf=1+k['gc_pages']/k['host_pages'] if good else '',sample_status='active_cumulative' if good else 'inactive_or_zero',source=str(f))
  row.update(k);w.writerow(row);count+=1
while proc.poll() is None:
 consume();(P/'status.txt').write_text('running_'+phase()+';samples='+str(count)+'\n');time.sleep(2)
consume();rc=proc.wait();console.close();ledger.close();issues=[]
result={'run_id':P.name,'exit_code':rc,'sample_rows':count,'started_at':start,'finished_at':datetime.now().astimezone().isoformat(),'raw_path':str(D),'measurement':meta['measurement'],'hostname':meta['hostname'],'machine_id':meta['machine_id'],'source_commit':meta['source_commit'],'module_sha256':meta['module_sha256']}
if rc:issues.append('runner_exit_nonzero')
validation=subprocess.run(['python3',str(P/'validate-results.py')],cwd=ROOT,capture_output=True,text=True)
(P/'validation.stdout.txt').write_text(validation.stdout)
(P/'validation.stderr.txt').write_text(validation.stderr)
if validation.returncode:issues.append('saved-evidence validator failed; see validation logs')
else:result.update(json.loads(validation.stdout))
result['issues']=issues;result['status']='validated_saved_evidence' if not issues else 'failed_or_incomplete_preserved'
(P/'completion-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(P/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(P/'exit-code.txt').write_text(str(rc if rc else (1 if issues else 0))+'\n')
(P/'status.txt').write_text(result['status']+'\n')
with (P/'journal.md').open('a') as f:f.write('\n- FINISHED '+json.dumps(result,ensure_ascii=False)+'\n')
with (ROOT/'EXPERIMENT_LOG.md').open('a') as f:f.write('\n- '+P.name+' FINISHED '+json.dumps(result,ensure_ascii=False)+'\n')
publish_rc=subprocess.call(['python3',str(P/'publish-results.py')],cwd=ROOT)
(P/'publish.exit').write_text(str(publish_rc)+'\n')
raise SystemExit(rc if rc else (1 if issues else publish_rc))
