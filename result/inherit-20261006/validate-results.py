"""Validate one saved mixV run; never issues device I/O."""
from pathlib import Path
from datetime import datetime
import sys,re,json,gzip,csv
P=Path(__file__).resolve().parent;policy,stage=sys.argv[1:];assert policy in ('fixed37','fixed50') and stage in ('fitcheck','long')
D=(P/'fitcheck' if stage=='fitcheck' else P)/f'mixV-{policy}-rep1'
smoke=False;secs=60 if stage=='fitcheck' else 4000;records=600000
meta=json.loads((P/'metadata.json').read_text())
def require(ok,msg):
 if not ok:raise AssertionError(msg)
def read(name):
 f=D/name
 if f.exists():return f.read_text(errors='replace')
 with gzip.open(str(f)+'.gz','rt',errors='replace') as g:return g.read()
def count(name):return {k:int(v) for k,v in re.findall(r'\b(epoch|active|host_bytes|host_pages|gc_pages)=(\d+)',read(name).splitlines()[0])}
def ts(name):return datetime.fromisoformat(read(name).strip()).timestamp()
def fio(name,expected=None):
 data=json.loads(read(name));jobs=data['jobs'];require(all(j['error']==0 for j in jobs),name+' fio error')
 written=sum(j['write']['io_bytes'] for j in jobs);require(written>0,name+' no writes')
 if expected is not None:require(written==expected,name+' requested bytes not complete')
 return jobs
require(read('exit-code.txt').strip()=='0','runner/cleanup exit not0')
a=count('started.txt');b=count('stopped.txt');z=count('final-control.txt');p=count('prepared.txt')
require(a['active']==1 and all(a[k]==0 for k in ['host_pages','host_bytes','gc_pages']),'zero start')
require(p['active']==0 and all(p[k]==0 for k in ['host_pages','host_bytes','gc_pages']),'preparation excluded')
require(b==z and b['active']==0 and b['epoch']==a['epoch'] and b['host_pages']>0 and b['gc_pages']>0,'stop counters/epoch')
parts=[{k:int(v) for k,v in re.findall(r'(host_pages|gc_pages|arm)=(\d+)',l)} for l in read('stopped.txt').splitlines()[1:] if l.startswith('part=')]
require(len(parts)==4 and all(p['arm']==int(policy[-2:]) for p in parts),'four partitions fixed requested arm')
require(all(sum(p[k] for p in parts)==b[k] for k in ['host_pages','gc_pages']),'partition totals')
before=int(read('block-stat-before.txt'));after=int(read('block-stat-after.txt'))
require(after==int(read('block-stat-stop-before.txt')) and b['host_bytes']==(after-before)*512,'block-stat/host-byte mismatch')
fio('preset.json',6*1024**3);fio('prepare.json',3*1024**3)
require(not (D/'phase-F-create.json').exists(),'FIO recreated instead of kept')
identities=[read(f'fio-file-{slot}-start.stat').strip().split() for slot in 'ABCDEFGHI']
require(all(len(x)==2 and int(x[1])==6*1024**3 for x in identities) and len({x[0] for x in identities})==1,'same6GiB FIO file retained')
expected={k:n*secs//600//(10 if smoke else 1) for k,n in [('hot',58982400000),('warm',29491200000),('cold',9830400000)]}
jobs=fio('phase-F.json',sum(expected.values()))
require(len(jobs)==3 and {j['jobname'] for j in jobs}==set(expected),'FIO jobs')
require(all(j['write']['io_bytes']==expected[j['jobname']] and j['write']['runtime']>=(secs/(10 if smoke else 1)-2)*1000 for j in jobs),'FIO duration/bytes')
def ycsb(name,load=False):
 text=read(name)
 require(not re.search(r'SQLITE_FULL|No space left on device|Exception in thread|Return=ERROR|ERROR:',text),name+' explicit error')
 returns=re.findall(r'^\[([^]]+)\], Return=([^,]+), (\d+)$',text,re.M)
 require(returns and not any(status!='OK' and int(n)>0 for _,status,n in returns),name+' operation failures')
 require(not re.search(r'^\[[^]]*-FAILED\], Operations, [1-9]',text,re.M),name+' failed operations')
 ok={op:int(n) for op,status,n in returns if status=='OK'}
 runtime=re.findall(r'^\[OVERALL\], RunTime\(ms\), ([\d.]+)$',text,re.M);require(len(runtime)==1,name+' runtime');seconds=float(runtime[0])/1000
 if load:require(ok.get('INSERT')==records,name+' record count')
 else:
  require(ok.get('READ',0)>0 and ok.get('UPDATE',0)>0,name+' successes')
  if smoke:require(sum(ok.values())==20000 or secs-5<=seconds<=secs+300,name+' neither operation cap nor time cap reached')
  else:require(secs-5<=seconds<=secs+300,name+' requested time not reached')
 return dict(runtime_seconds=seconds,successful_operations=ok)
loads={slot:ycsb(f'ycsb-load-{slot}.txt',True) for slot in 'ADH'}
phases=[];endlast=None
for slot,name in zip('ABCDEFGHI',meta['phase_order']):
 start,end=ts(f'phase-{slot}-start.time'),ts(f'phase-{slot}-end.time')
 require(end>=start and (endlast is None or start>=endlast),slot+' timing order');endlast=end
 c0,c1=count(f'phase-{slot}-start.txt'),count(f'phase-{slot}-end.txt')
 require(c0['active']==c1['active']==1 and c0['epoch']==c1['epoch']==a['epoch'],slot+' measurement continuity')
 d={k:c1[k]-c0[k] for k in ['host_bytes','host_pages','gc_pages']};require(d['host_pages']>0 and d['host_bytes']>0 and d['gc_pages']>=0,slot+' counts')
 detail={}
 if name.startswith('YCSB'):detail=ycsb(f'ycsb-run-{slot}.txt')
 elif name!='FIO-Fast':
  text=read(f'filebench-{slot}.txt');require(not re.search(r'ENOSPC|No space left on device|IO error|Failed to|failed to',text,re.I),slot+' Filebench failure')
  starts=re.findall(r'^([\d.]+): Running\.\.\.$',text,re.M);ends=re.findall(r'^([\d.]+): IO Summary:',text,re.M)
  n,rt=(4,secs//4) if name=='OLTP' else (1,secs)
  require(len(starts)==len(ends)==n,slot+' Filebench chunks');times=[float(e)-float(s) for s,e in zip(starts,ends)]
  require(all(rt<=t<rt+60 for t in times),slot+' Filebench duration');detail={'process_runtimes_seconds':times}
 if not smoke:require(end-start>=secs-5,slot+' long duration')
 phases.append(dict(slot=slot,workload=name,actual_seconds=end-start,waf=1+d['gc_pages']/d['host_pages'],**d,**detail))
require(len(re.findall(r'^phase[A-I]\(',read('summary.txt'),re.M))==9,'nine summary phases')
# Physical file extent snapshots, in4KiB filesystem blocks; not a trace of all dynamic writes.
def merge(xs):
 out=[]
 for a,b in sorted(xs):
  if out and a<=out[-1][1]:out[-1]=(out[-1][0],max(b,out[-1][1]))
  else:out.append((a,b))
 return out
extents={}
for f in D.glob('extents-*.txt'):
 xs=[]
 for l in f.read_text(errors='replace').splitlines():
  m=re.match(r'\s*\d+:\s*\d+\.\.\s*\d+:\s*(\d+)\.\.\s*(\d+):\s*(\d+):',l)
  if m and not any(s in l for s in ['unknown_loc','delalloc','unwritten']):xs.append((int(m[1]),int(m[2])+1))
 extents[f.stem]=merge(xs)
for slot in 'ABCDEFGHI':require(bool(extents.get(f'extents-{slot}-files')),slot+' no usable physical extent snapshot')
# Table3 prep uses kept test.dat, no fill.dat extent required.
def amount(xs):return sum(b-a for a,b in xs)
def intersect(xs,ys):
 i=j=total=0
 while i<len(xs) and j<len(ys):
  a,b=xs[i];c,d=ys[j];total+=max(0,min(b,d)-max(a,c))
  if b<d:i+=1
  else:j+=1
 return total
rows=[]
for prev,cur in zip('ABCDEFGH','BCDEFGHI'):
 x=extents[f'extents-{prev}-files'];y=extents[f'extents-{cur}-files'];n=intersect(x,y)
 rows.append(dict(previous=prev,current=cur,overlap_blocks_4KiB=n,previous_snapshot_blocks=amount(x),current_snapshot_blocks=amount(y),fraction_current_snapshot_overlapping_previous=n/amount(y),scope='end-of-phase saved-file extent snapshots; excludes files deleted during workloads and metadata'))
with (D/'extent-overlap.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
series=[]
for l in read('control-series.txt').splitlines():
 kv={k:int(v) for k,v in re.findall(r'\b(epoch|active|host_bytes|host_pages|gc_pages)=(\d+)',l)}
 if len(kv)!=5 or not l.split()[0].isdigit():continue
 stamp=int(l.split()[0]);series.append(dict(unix_timestamp=stamp,**kv,cumulative_waf=1+kv['gc_pages']/kv['host_pages'] if kv['active'] and kv['host_pages'] else ''))
require(series,'no30s samples')
with (D/'waf-series.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(series[0]));w.writeheader();w.writerows(series)
print(json.dumps(dict(status='validated_saved_evidence',policy=policy,stage=stage,waf=1+b['gc_pages']/b['host_pages'],host_bytes=b['host_bytes'],host_pages=b['host_pages'],gc_pages=b['gc_pages'],actual_measured_seconds=ts('phase-I-end.time')-ts('phase-A-start.time'),loads=loads,phases=phases,extent_overlaps=rows,sample_rows=len(series),measurement='FTL page WAF, block-stat verifies host bytes; no independent NAND measurement'),indent=2))
