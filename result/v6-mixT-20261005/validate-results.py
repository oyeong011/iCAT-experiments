"""Read-only validation of all nine mixT phases; never launches experiments."""
from pathlib import Path
from datetime import datetime
import re,json,gzip,csv,sys
P=Path(__file__).resolve().parent;stage=sys.argv[1];require_stage=stage in ('smoke','long');assert require_stage
D=P/('mixT-onlinev6-rep1-smoke' if stage=='smoke' else 'mixT-onlinev6-rep1')
meta=json.loads((P/'metadata.json').read_text());secs=120 if stage=='smoke' else 4000
meta['expected_fio_bytes']={k:n*secs//600 for k,n in [('hot',58982400000),('warm',29491200000),('cold',9830400000)]}
def require(condition,message):
 if not condition:raise AssertionError(message)
def read(name):
 p=D/name
 if p.exists():return p.read_text()
 with gzip.open(str(p)+'.gz','rt') as f:return f.read()
def counters(name):
 return {k:int(v) for k,v in re.findall(r'\b(epoch|active|host_bytes|host_pages|gc_pages)=(\d+)',read(name).splitlines()[0])}
def timestamp(name):return datetime.fromisoformat(read(name).strip()).timestamp()
def check_fio(name,expected):
 jobs=json.loads(read(name))['jobs']
 require(all(j['error']==0 for j in jobs),name+' fio error')
 require(sum(j['write']['io_bytes'] for j in jobs)==expected,name+' requested write bytes')
 return jobs
require(read('exit-code.txt').strip()=='0','runner nonzero including stop/block-stat/cleanup checks')
a=counters('started.txt');b=counters('stopped.txt');prepared=counters('prepared.txt');z=counters('final-control.txt')
require(a['active']==1 and all(a[k]==0 for k in ['host_bytes','host_pages','gc_pages']),'zero start')
require(prepared['active']==0 and all(prepared[k]==0 for k in ['host_bytes','host_pages','gc_pages']),'unmeasured preparation')
require(b==z and b['active']==0 and b['epoch']==a['epoch'] and b['host_pages']>0,'stop/final epoch/counters')
parts=[dict((k,int(v)) for k,v in re.findall(r'(host_pages|gc_pages|arm)=(\d+)',line)) for line in read('stopped.txt').splitlines()[1:] if line.startswith('part=')]
require(len(parts)==4 and all(0<=p['arm']<60 for p in parts),'four adaptive partitions')
require(all(sum(p[k] for p in parts)==b[k] for k in ['host_pages','gc_pages']),'partition totals')
check_fio('preset.json',6*1024**3);check_fio('prepare.json',3*1024**3)
require(all(re.search(r'WATGC_V2 sample .*part='+str(part)+r' ',read('kernel.log')) for part in range(4)),'learner sample evidence all partitions')
# YCSB operation successes and runtime; time-capped runs need not finish the 1e9 safety cap.
def ycsb(name,load=False):
 text=read(name)
 failures=[(op,status,int(n)) for op,status,n in re.findall(r'^\[([^]]+)\], Return=([^,]+), (\d+)$',text,re.M) if status!='OK' and int(n)>0]
 require(not failures,name+' operation errors '+str(failures))
 require(not re.search(r'^\[[^]]*-FAILED\], Operations, [1-9]\d*$',text,re.M),name+' failed operations')
 ok={op:int(n) for op,n in re.findall(r'^\[([^]]+)\], Return=OK, (\d+)$',text,re.M)}
 if load:require(ok.get('INSERT')==250000,'complete initial 250000-record load')
 else:require(ok.get('READ',0)>0 and ok.get('UPDATE',0)>0,name+' read/update successes')
 runtimes=re.findall(r'^\[OVERALL\], RunTime\(ms\), ([\d.]+)$',text,re.M)
 require(len(runtimes)==1,name+' runtime summary')
 seconds=float(runtimes[0])/1000
 if not load:require(secs-5<=seconds<=secs+300,name+' requested timed runtime')
 return {'runtime_seconds':seconds,'successful_operations':ok}
load=ycsb('ycsb-load.txt',True)
require(re.search(r'^run '+str(secs//4)+r'$',read('oltp.f'),re.M),'OLTP chunk profile')
require(re.search(r'^run '+str(secs)+r'$',read('varmail.f'),re.M),'Varmail profile')
phases=[];previous_end=None
for slot,name in zip('ABCDEFGHI',meta['phase_order']):
 start=timestamp(f'phase-{slot}-start.time');end=timestamp(f'phase-{slot}-end.time');seconds=end-start
 require(seconds>=secs-5,slot+' phase too short')
 if previous_end is not None:require(start>=previous_end,slot+' order')
 previous_end=end
 c0=counters(f'phase-{slot}-start.txt');c1=counters(f'phase-{slot}-end.txt')
 require(c0['active']==c1['active']==1 and c0['epoch']==c1['epoch']==a['epoch'],slot+' continuous measurement epoch')
 dh=c1['host_pages']-c0['host_pages'];dg=c1['gc_pages']-c0['gc_pages'];db=c1['host_bytes']-c0['host_bytes']
 require(dh>0 and dg>=0 and db>0,slot+' counters')
 detail={}
 if name.startswith('YCSB'):detail=ycsb(f'ycsb-run-{slot}.txt')
 elif name=='FIO-Fast':
  jobs=check_fio(f'phase-{slot}.json',sum(meta['expected_fio_bytes'].values()))
  require(len(jobs)==3 and {j['jobname'] for j in jobs}==set(meta['expected_fio_bytes']),'FIO job identity')
  require(all(j['write']['io_bytes']==meta['expected_fio_bytes'][j['jobname']] and j['write']['runtime']>=(secs-5)*1000 for j in jobs),'FIO job bytes/duration')
 else:
  text=read(f'filebench-{slot}.txt');starts=re.findall(r'^([\d.]+): Running\.\.\.$',text,re.M);ends=re.findall(r'^([\d.]+): IO Summary:',text,re.M)
  n,rt=(4,secs//4) if name=='OLTP' else (1,secs)
  require(len(starts)==len(ends)==n,slot+' Filebench completions')
  times=[float(e)-float(s) for s,e in zip(starts,ends)]
  require(all(rt<=t<rt+60 for t in times),slot+' Filebench runtime')
  detail={'process_runtimes_seconds':times}
 phases.append(dict(slot=slot,workload=name,actual_seconds=seconds,host_bytes=db,host_pages=dh,gc_pages=dg,waf=1+dg/dh,**detail))
rows=list(csv.DictReader((D/'waf-series.csv').open()));active=[r for r in rows if r['cumulative_waf']]
require(all(abs(float(r['cumulative_waf'])-(1+int(r['gc_pages'])/int(r['host_pages'])))<1e-12 for r in active),'CSV WAF formula')
print(json.dumps(dict(waf=1+b['gc_pages']/b['host_pages'],host_bytes=b['host_bytes'],host_pages=b['host_pages'],gc_pages=b['gc_pages'],phases=phases,actual_measured_seconds=timestamp('phase-I-end.time')-timestamp('phase-A-start.time'),initial_load=load,active_sample_rows=len(active),block_stat_validation='upstream runner stop boundary and host_bytes assertion passed; not independent NAND measurement'),indent=2))
