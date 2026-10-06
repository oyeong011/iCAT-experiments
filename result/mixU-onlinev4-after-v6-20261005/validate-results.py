"""Read saved mixU evidence, validate eight phases and export learning events."""
from pathlib import Path
from datetime import datetime
import json,re,csv
P=Path(__file__).resolve().parent;meta=json.loads((P/'metadata.json').read_text());D=P/f"mixU-{meta['policy']}-rep1"
def require(c,m):
 if not c:raise AssertionError(m)
def read(n):return (D/n).read_text()
def kv(n):return {k:int(v) for k,v in re.findall(r'\b(epoch|active|host_bytes|host_pages|gc_pages)=(\d+)',read(n).splitlines()[0])}
def ts(n):return datetime.fromisoformat(read(n).strip()).timestamp()
# Retain learning information even if final measurement verification fails.
learning=[];slot='preparation';kernel=read('kernel.log')
for line in kernel.splitlines():
 marker=re.search(r'phase=([A-H]) START',line)
 if marker:slot=marker[1]
 event=re.search(r'WATGC_V2 ([\w-]+)\s+(.*)',line)
 if not event:continue
 stamp=re.search(r'\[\s*([\d.]+)\]',line)
 vals=dict(re.findall(r'([a-zA-Z_][\w]*)=([^\s]+)',event[2]))
 vals.update(event=event[1],kernel_seconds=stamp[1] if stamp else '',workload_slot=slot,raw_line=line)
 learning.append(vals)
if learning:
 fields=['kernel_seconds','workload_slot','event']+sorted(set().union(*(r.keys() for r in learning))-{'kernel_seconds','workload_slot','event','raw_line'})+['raw_line']
 with (P/'learning-events.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(learning)
require(read('exit-code.txt').strip()=='0','runner exit including blockstat/cleanup checks')
a=kv('started.txt');b=kv('stopped.txt');z=kv('final-control.txt');c=kv('prepared.txt')
require(a['active']==1 and all(a[k]==0 for k in ['host_bytes','host_pages','gc_pages']),'zero start')
require(c['active']==0 and all(c[k]==0 for k in ['host_bytes','host_pages','gc_pages']),'preparation unmeasured')
require(b==z and b['active']==0 and b['epoch']==a['epoch'] and b['host_pages']>0,'stop and final')
parts=[dict((k,int(v)) for k,v in re.findall(r'(host_pages|gc_pages|arm)=(\d+)',line)) for line in read('stopped.txt').splitlines()[1:] if line.startswith('part=')]
require(len(parts)==4 and all(sum(p[k] for p in parts)==b[k] for k in ['host_pages','gc_pages']),'partition totals')
if meta['policy']=='onlinev4':
 require(all(any(r['event']=='sample' and r.get('part')==str(part) for r in learning) for part in range(4)),'learner samples for all4 parts')
else:
 require(all(p['arm']==meta['arm'] for p in parts) and 'Fixed CAT init' in kernel,'fixed policy identity')
def fio(n,expected):
 jobs=json.loads(read(n))['jobs'];require(all(j['error']==0 for j in jobs),n+' fio errors');require(sum(j['write']['io_bytes'] for j in jobs)==expected,n+' requested bytes');return jobs
fio('preset.json',6*1024**3);fio('prepare.json',3*1024**3)
require(re.search(r'^run 4500$',read('varmail.f'),re.M),'Varmail profile4500')
phases=[];prev=None
for slot,workload in zip('ABCDEFGH',meta['phase_order']):
 start=ts(f'phase-{slot}-start.time');end=ts(f'phase-{slot}-end.time');elapsed=end-start
 require(elapsed>=4490,slot+' phase too short')
 if prev is not None:require(start>=prev,slot+' phase order')
 prev=end
 x=kv(f'phase-{slot}-start.txt');y=kv(f'phase-{slot}-end.txt')
 require(x['active']==y['active']==1 and x['epoch']==y['epoch']==a['epoch'],slot+' measurement continuity')
 delta={k:y[k]-x[k] for k in ['host_bytes','host_pages','gc_pages']}
 require(delta['host_pages']>0 and delta['host_bytes']>0 and delta['gc_pages']>=0,slot+' counters')
 detail={}
 if workload=='FIO-Fast':
  jobs=fio(f'phase-{slot}.json',sum(meta['expected_fio_bytes'].values()))
  require(len(jobs)==3 and {j['jobname'] for j in jobs}==set(meta['expected_fio_bytes']),'FIO job identity')
  require(all(j['write']['io_bytes']==meta['expected_fio_bytes'][j['jobname']] and j['write']['runtime']>=4490*1000 for j in jobs),'FIO bytes/runtime')
  detail['requested_write_bytes']=sum(meta['expected_fio_bytes'].values())
 else:
  t=read(f'filebench-{slot}.txt');starts=re.findall(r'^([\d.]+): Running\.\.\.$',t,re.M);ends=re.findall(r'^([\d.]+): IO Summary:',t,re.M)
  require(len(starts)==len(ends)==1,slot+' Filebench completion')
  rt=float(ends[0])-float(starts[0]);require(4500<=rt<4560,slot+' Varmail runtime');detail['process_runtime_seconds']=rt
 phases.append(dict(slot=slot,workload=workload,actual_seconds=elapsed,waf=1+delta['gc_pages']/delta['host_pages'],**delta,**detail))
rows=list(csv.DictReader((P/'waf-series.csv').open()));active=[r for r in rows if r['cumulative_waf']]
require(all(abs(float(r['cumulative_waf'])-(1+int(r['gc_pages'])/int(r['host_pages'])))<1e-12 for r in active),'CSV WAF formula')
events={kind:sum(r['event']==kind for r in learning) for kind in sorted({r['event'] for r in learning})}
print(json.dumps(dict(waf=1+b['gc_pages']/b['host_pages'],host_bytes=b['host_bytes'],host_pages=b['host_pages'],gc_pages=b['gc_pages'],phases=phases,actual_measured_seconds=ts('phase-H-end.time')-ts('phase-A-start.time'),active_sample_rows=len(active),learning_event_counts=events,learning_note='Kernel learner epoch differs from measurement epoch; preparation events labeled separately; event presence does not prove convergence',block_stat_validation='upstream runner assertions passed; no independent NAND claim'),indent=2))
