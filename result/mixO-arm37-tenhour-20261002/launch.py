#!/usr/bin/env python3
if __name__ != '__main__':
 raise ImportError('Explicit experiment launch only')
import os,csv,json,re,time,subprocess,fcntl
from pathlib import Path
from datetime import datetime
P=Path(__file__).resolve().parent;ROOT=P.parents[1];D=P/'mixO-arm37-rep1'
lock=(P/'campaign.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not D.exists(),'Refusing overwrite'
assert not Path('/sys/module/nvmev').exists(),'Virtual module occupied; no reset'
assert subprocess.run(['mountpoint','-q',str(ROOT/'mnt')]).returncode!=0,'Mount occupied'
meta=json.loads((P/'metadata.json').read_text());env=os.environ.copy()
for k in ['SMOKE','VM_FILES']:env.pop(k,None)
env.update(MULT='1',VM_RUN='18000',DEV='/dev/nvme1n1')
(P/'status.txt').write_text('running_preparation\n')
start=datetime.now().astimezone().isoformat();meta['started_at']=start;(P/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
console=(P/'mixO-arm37.console.txt').open('w')
proc=subprocess.Popen(['bash',str(P/'runner.sh'),'mixO','arm37','1'],cwd=ROOT,env=env,stdout=console,stderr=subprocess.STDOUT)
(P/'runner.pid').write_text(str(proc.pid)+'\n')
ledger=(P/'waf-series.csv').open('w',newline='',buffering=1)
fields=['unix_timestamp','iso_time','elapsed_measured_seconds','phase','epoch','active','host_bytes','host_pages','gc_pages','cumulative_waf','sample_status','source']
w=csv.DictWriter(ledger,fieldnames=fields);w.writeheader();offset=0;count=0

def phase():
 if (D/'phase-B-start.time').exists():return 'Varmail'
 if (D/'phase-A-start.time').exists():return 'OLTP'
 return 'preparation'

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
  row=dict(unix_timestamp=int(ts),iso_time=datetime.fromtimestamp(int(ts)).astimezone().isoformat(),elapsed_measured_seconds=elapsed,phase=phase(),cumulative_waf=1+k['gc_pages']/k['host_pages'] if good else '',sample_status='active_cumulative' if good else 'inactive_or_zero',source=str(f))
  row.update(k);w.writerow(row);count+=1
while proc.poll() is None:
 consume();(P/'status.txt').write_text('running_'+phase()+';samples='+str(count)+'\n');time.sleep(2)
consume();rc=proc.wait();console.close();ledger.close();issues=[]
result={'run_id':P.name,'exit_code':rc,'sample_rows':count,'started_at':start,'finished_at':datetime.now().astimezone().isoformat(),'raw_path':str(D),'measurement':'manual continuous OLTP18000 -> Varmail18000','hostname':meta['hostname'],'machine_id':meta['machine_id'],'source_commit':meta['source_commit'],'module_sha256':meta['module_sha256']}
if rc:issues.append('runner_exit_nonzero')
try:
 def kv(name):return {a:int(b) for a,b in re.findall(r'\b(active|host_bytes|host_pages|gc_pages)=(\d+)',(D/name).read_text().splitlines()[0])}
 a=kv('started.txt');b=kv('stopped.txt');c=kv('prepared.txt');z=kv('final-control.txt')
 assert a['active']==1 and all(a[k]==0 for k in ('host_bytes','host_pages','gc_pages')),'start'
 assert all(c[k]==0 for k in ('host_bytes','host_pages','gc_pages')),'prepared'
 assert b['active']==0 and b==z and b['host_pages']>0,'stop/final'
 part=[{k:int(v) for k,v in re.findall(r'(host_pages|gc_pages)=(\d+)',line)} for line in (D/'stopped.txt').read_text().splitlines()[1:] if line.startswith('part=')]
 assert len(part)==4 and all(sum(p[k] for p in part)==b[k] for k in ('host_pages','gc_pages')),'partition counters'
 for fn,nbytes in [('preset.json',6*1024**3),('prepare.json',3*1024**3)]:
  j=json.loads((D/fn).read_text());assert all(x['error']==0 for x in j['jobs']),'fio errors';assert sum(x['write']['io_bytes'] for x in j['jobs'])==nbytes,'prepared requested I/O'
 phases=[]
 for slot,profile in [('A','oltp.f'),('B','varmail.f')]:
  assert re.search(r'^run 18000$',(D/profile).read_text(),re.M),'profile duration'
  text=(D/f'filebench-{slot}.txt').read_text();assert 'IO Summary' in text,'Filebench completion'
  m=re.search(r'IO Summary:.*? ([\d.]+)s\s*$',text,re.M)
  if m:assert abs(float(m[1])-18000)<60,'Filebench runtime'
  sec=(datetime.fromisoformat((D/f'phase-{slot}-end.time').read_text().strip())-datetime.fromisoformat((D/f'phase-{slot}-start.time').read_text().strip())).total_seconds()
  assert 18000<=sec<=18600,'actual phase duration'
  phases.append({'slot':slot,'actual_seconds':sec,'profile':profile})
 result.update(waf=1+b['gc_pages']/b['host_pages'],host_bytes=b['host_bytes'],host_pages=b['host_pages'],gc_pages=b['gc_pages'],phases=phases,actual_measured_seconds=sum(x['actual_seconds'] for x in phases))
 assert 'Fixed CAT init' in (D/'kernel.log').read_text() and 'arm=37 ' in (D/'kernel.log').read_text(),'observed arm'
except Exception as e:issues.append(str(e))
result['issues']=issues;result['status']='validated_saved_evidence' if not issues else 'failed_or_incomplete_preserved'
(P/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(P/'exit-code.txt').write_text(str(rc if rc else (1 if issues else 0))+'\n')
(P/'status.txt').write_text(result['status']+'\n')
with (P/'journal.md').open('a') as f:f.write('\n- FINISHED '+json.dumps(result,ensure_ascii=False)+'\n')
with (ROOT/'EXPERIMENT_LOG.md').open('a') as f:f.write('\n- '+P.name+' FINISHED '+json.dumps(result,ensure_ascii=False)+'\n')
raise SystemExit(rc if rc else (1 if issues else 0))
