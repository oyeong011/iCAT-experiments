if __name__ != '__main__':
 raise ImportError('Campaign runner may only execute as explicit main')
#!/usr/bin/env python3
import csv,json,os,re,subprocess,fcntl,time,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
assert not (P/'HALTED.txt').exists(),'Campaign HALTED; do not execute'
assert (ROOT/'result/handoff-f299c51e-20261002-r2/validation.exit').read_text().strip()=='0','Validation PASS required'
meta=json.loads((P/'metadata.json').read_text());mixes=meta['workloads'];rows=[];results=[]
lock=(P/'campaign.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def journal(t):
 with (P/'journal.md').open('a') as f:f.write('\n- '+time.strftime('%Y-%m-%d %H:%M:%S')+' '+t+'\n')
def csvwrite(name,data,keys):
 tmp=P/(name+'.tmp')
 with tmp.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(data)
 tmp.replace(P/name)
def save():
 csvwrite('status.csv',rows,['run','workload','policy','MULT','VM_RUN','status','exit','issues','path'])
 csvwrite('results.csv',results,['run','workload','policy','arm','MULT','VM_RUN','waf','host_bytes','host_pages','gc_pages','hostname','machine_id','measurement','actual_seconds','seed','preparation','source_commit','source_local_changes','kernel','module_sha256','status','path'])
 csvwrite('inventory.csv',results,['run','workload','policy','arm','MULT','VM_RUN','waf','host_bytes','host_pages','gc_pages','hostname','machine_id','measurement','actual_seconds','seed','preparation','source_commit','source_local_changes','kernel','module_sha256','status','path'])
 refs=[]
 for r in results:
  pool=[q for q in results if q['workload']==r['workload'] and q['MULT']==r['MULT']]
  refs.append(dict(workload=r['workload'],MULT=r['MULT'],arm=r['arm'],waf=r['waf'],rank=1+sum(q['waf']<r['waf'] for q in pool),pool_n=len(pool),measurement=r['measurement'],hostname=r['hostname'],path=r['path']))
 csvwrite('rank-reference.csv',refs,['workload','MULT','arm','waf','rank','pool_n','measurement','hostname','path'])
 pairs=[]
 for r in results:
  other=next((q for q in results if q['workload']==r['workload'] and q['arm']==r['arm'] and q['MULT']==3),None)
  if r['MULT']==1 and other:pairs.append(dict(workload=r['workload'],arm=r['arm'],waf_x1=r['waf'],waf_x3=other['waf'],relative_percent=100*(other['waf']/r['waf']-1),path_x1=r['path'],path_x3=other['path']))
 csvwrite('convergence.csv',pairs,['workload','arm','waf_x1','waf_x3','relative_percent','path_x1','path_x3'])
def validate(d,lb,arm,mult):
 def kv(n):return {k:int(v) for k,v in re.findall(r'\b(active|host_bytes|host_pages|gc_pages)=(\d+)',(d/n).read_text().splitlines()[0])}
 assert not (d/'SUSPECT.txt').exists(),'SUSPECT preserved'
 assert (d/'exit-code.txt').read_text().strip()=='0','exit'
 a=kv('started.txt');b=kv('stopped.txt');c=kv('prepared.txt');z=kv('final-control.txt')
 assert a.get('active')==1 and all(a.get(k,-1)==0 for k in ('host_bytes','host_pages','gc_pages')),'start'
 assert all(c.get(k,-1)==0 for k in ('host_bytes','host_pages','gc_pages')),'prepare'
 assert b.get('active')==0 and b==z and b['host_pages']>0,'stop'
 part=[{k:int(v) for k,v in re.findall(r'(host_pages|gc_pages)=(\d+)',l)} for l in (d/'stopped.txt').read_text().splitlines()[1:] if l.startswith('part=')]
 assert len(part)==4 and all(sum(q[k] for q in part)==b[k] for k in ('host_pages','gc_pages')),'partition sum'
 assert f'arm={arm} ' in (d/'kernel.log').read_text(),'kernel arm'
 for filename,required in [('preset.json',6*1024**3),('prepare.json',3*1024**3)]:
  assert sum(j.get('write',{}).get('io_bytes',0) for j in json.loads((d/filename).read_text())['jobs'])==required,filename+': preparation incomplete'
 for f in d.glob('*.json'):
  for job in json.loads(f.read_text()).get('jobs',[]):
   assert job.get('error',0)==0,(f.name,'fio error')
   m=re.fullmatch(r'(\d+)([KMG]?)',str(job.get('job options',{}).get('io_size','')),re.I)
   if m:assert job['write']['io_bytes']==int(m[1])*{'':1,'K':1024,'M':1024**2,'G':1024**3}[m[2].upper()],(f.name,'requested I/O')
 records=250000 if lb=='mixP' else 600000 if lb in ['mixJ','mixB','mixH','mixG'] else 0
 ops=4000000*mult if records else 0
 subprocess.run(['python3',str(P/'validate-application.py'),str(d),str(records),str(ops),str(300*mult)],check=True)
 assert (d/'HOST.txt').read_text().strip()==meta['hostname'],'host'
 assert (d/'machine-id.txt').read_text().strip()==meta['machine_id'],'machine_id'
 secs=0
 from datetime import datetime
 for slot in 'ABC':
  a=d/f'phase-{slot}-start.time';e=d/f'phase-{slot}-end.time'
  if a.exists() and e.exists():secs+=(datetime.fromisoformat(e.read_text().strip())-datetime.fromisoformat(a.read_text().strip())).total_seconds()
 return b,secs
def publish(msg):
 rc=subprocess.call(['python3',str(P/'publish.py'),msg],stdout=(P/'publish.log').open('a'),stderr=subprocess.STDOUT)
 if rc:journal('PUSH_FAILED icat-2; preserve results; exit='+str(rc));raise RuntimeError('icat-2 publish failed')
def tools(d,stage):
 for tool in [['fio','--version'],['sqlite3','--version'],['java','-version']]:
  with (P/'tool-checks.txt').open('a') as log:
   rc=subprocess.call(tool,stdout=log,stderr=subprocess.STDOUT)
  if rc:
   if d.exists():(d/'SUSPECT.txt').write_text('Tool failed '+str(tool)+' '+stage+'; preserved; queue stopped\n')
   raise RuntimeError('Tool validation failed '+str(tool))
def run(lb,arm,mult):
 pol=f'arm{arm:02d}';name=f'{lb}-{pol}-rep1'+(f'-x{mult}' if mult!=1 else '');d=P/name
 row=dict(run=name,workload=lb,policy=pol,MULT=mult,VM_RUN=300*mult,status='pending',exit='',issues='',path=str(d));rows.append(row);save()
 if d.exists():
  try:b,secs=validate(d,lb,arm,mult);row['status']='reused_validated'
  except Exception as e:row['status']='existing_invalid_preserved';row['issues']=str(e);save();raise RuntimeError('Existing incomplete/failed run preserved; review before resuming:'+name)
 else:
  assert not Path('/sys/module/nvmev').exists(),'Another module/run occupies device'
  assert shutil.disk_usage(ROOT).free>=5*1024**3,'Less than5GiB result space'
  tools(d,'before');row['status']='running';save();journal(f'START {name}; module nvmev-{pol}.ko; MULT={mult} VM_RUN={300*mult}, rep1; source/CPU/module/device metadata recorded; runner output routing only changes.')
  env=os.environ.copy();env.update(MULT=str(mult),VM_RUN=str(300*mult),DEV='/dev/nvme1n1')
  with (P/(name+'.console.txt')).open('w') as f:rc=subprocess.call(['bash',str(P/'runner.sh'),lb,pol,'1'],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
  row['exit']=rc
  if d.exists():(d/'HOST.txt').write_text(meta['hostname']+'\n');(d/'machine-id.txt').write_text(meta['machine_id']+'\n')
  if rc:row['status']='failed_preserved';save();raise RuntimeError('Run failed:'+name)
  tools(d,'after')
  try:b,secs=validate(d,lb,arm,mult)
  except Exception as e:row['status']='validation_failed_preserved';row['issues']=str(e);save();raise
  row['status']='validated';save()
 results.append(dict(run=name,workload=lb,policy=pol,arm=arm,MULT=mult,VM_RUN=300*mult,waf=1+b['gc_pages']/b['host_pages'],host_bytes=b['host_bytes'],host_pages=b['host_pages'],gc_pages=b['gc_pages'],hostname=meta['hostname'],machine_id=meta['machine_id'],measurement='manual_start_stop',actual_seconds=secs,seed='fio_hot=20260911;warm=20261011;cold=20261111;YCSB_seed=workload_default_unrecorded',preparation='6GiB_seq128k;3GiB_random4k_seed20260907_IOPS10000',source_commit=meta['source_commit'],source_local_changes=str(P/'source-status.txt'),kernel=meta['kernel'],module_sha256=__import__('hashlib').sha256((ROOT/'buildoutput'/('nvmev-'+pol+'.ko')).read_bytes()).hexdigest(),status='validated_saved_evidence',path=str(d)))
 save();journal(f'FINISH {name}: exit0, WAF={results[-1]["waf"]:.9f}, host_bytes={b["host_bytes"]}, seconds={secs}; counter/stop/FIO/YCSB/profile validated; block-stat assertion in runner passed.')
try:
 for lb in mixes:
  for arm in range(60):run(lb,arm,1)
  publish(lb+' all60 fixed CAT x1')
 journal('SWEEPDONE stage1')
 for lb in mixes:
  pool=[r for r in results if r['workload']==lb and r['MULT']==1];assert len(pool)==60
  top=sorted(pool,key=lambda r:(r['waf'],r['arm']))[:5]
  journal(lb+' top5 from60 x1: '+','.join(str(r['arm']) for r in top))
  for r in top:run(lb,r['arm'],3)
  publish(lb+' top5 fixed CAT x3')
 journal('QUEUE33DONE');(P/'queue.exit').write_text('0\n')
except Exception as e:
 journal('STOPPED '+repr(e));(P/'queue.exit').write_text('1\n')
 try:publish('QUEUE33 stopped; preserved failure evidence')
 except Exception:pass
 raise
