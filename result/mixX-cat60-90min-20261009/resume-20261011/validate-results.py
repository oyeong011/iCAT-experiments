"""Validation of preregistered90min CATgrid phases; never launches workloads."""
from pathlib import Path
from datetime import datetime
import json,re,sys,csv,gzip
P=Path(__file__).resolve().parent;policy=sys.argv[1];assert re.fullmatch(r'arm[0-5][0-9]',policy)
D=Path(sys.argv[2]) if len(sys.argv)>2 else P/f'mixX-{policy}-rep1'
meta=json.loads((P/'metadata.json').read_text());secs=meta['phase_seconds'];stage='screen90'
slots=meta['phase_slots'];names=meta['phase_order']
def require(ok,message):
 if not ok:raise AssertionError(message)
def read(n):
 f=D/n
 if f.exists():return f.read_text(errors='replace')
 with gzip.open(str(f)+'.gz','rt',errors='replace') as x:return x.read()
def cnt(n):return {k:int(v) for k,v in re.findall(r'\b(epoch|active|host_bytes|host_pages|gc_pages)=(\d+)',read(n).splitlines()[0])}
def ts(n):return datetime.fromisoformat(read(n).strip()).timestamp()
def fio(n,wanted):
 jobs=json.loads(read(n))['jobs'];require(jobs and all(j['error']==0 for j in jobs),n+' fio error')
 require(sum(j['write']['io_bytes'] for j in jobs)==wanted,n+' write completion')
 return jobs
require(read('exit-code.txt').strip()=='0','runner including cleanup failed')
a,b,z,p=cnt('started.txt'),cnt('stopped.txt'),cnt('final-control.txt'),cnt('prepared.txt')
fields=['host_bytes','host_pages','gc_pages']
require(a['active']==1 and all(a[k]==0 for k in fields),'zero start')
require(p['active']==0 and all(p[k]==0 for k in fields),'unmeasured prep')
require(b==z and b['active']==0 and b['epoch']==a['epoch'] and b['host_pages']>0 and b['gc_pages']>0,'final measurement counters')
parts=[{k:int(v) for k,v in re.findall(r'(host_pages|gc_pages|arm)=(\d+)',l)} for l in read('stopped.txt').splitlines()[1:] if l.startswith('part=')]
require(len(parts)==4 and all(x['arm']==int(policy[-2:]) for x in parts),'fixed policy all4partitions')
require(all(sum(x[k] for x in parts)==b[k] for k in ['host_pages','gc_pages']),'parts sum')
arm=int(policy[-2:]);expected_params=([2,4,7,10][arm//15],[25,50,100,200,400][arm//3%5],[4,7,16][arm%3])
init=[tuple(map(int,x)) for x in re.findall(r'Fixed CAT init ns=0 part=(\d+) arm=(\d+) k=(\d+) scale_pct=(\d+) age_ratio=(\d+)',read('kernel.log'))]
require(set((x[0],x[1],*x[2:]) for x in init)==set((p,arm,*expected_params) for p in range(4)),'module runtime grid mapping')

before,after=int(read('block-stat-before.txt')),int(read('block-stat-after.txt'))
require(after==int(read('block-stat-stop-before.txt')) and (after-before)*512==b['host_bytes'],'host bytes vs blockstat')
fio('preset.json',6*1024**3);fio('prepare.json',3*1024**3)
identities=[read(f'fio-file-{s}-start.stat').strip().split() for s in slots]
require(all(len(x)==2 and int(x[1])==6*1024**3 for x in identities) and len({x[0] for x in identities})==1,'kept6GiBfile')
require(not list(D.glob('phase-*-create.json')),'unexpected FIO recreation')
require(read('ycsb-load.txt').strip()==read('ycsb-run.txt').strip()=='','unexpected YCSB work')
expected={k:n*secs//600 for k,n in [('hot',58982400000),('warm',29491200000),('cold',9830400000)]}
regions={'hot':('0','512M'),'warm':('512M','1536M'),'cold':('2G','4G')}
summary={s:(int(h),int(g),float(w)) for s,h,g,w in re.findall(r'^phase(S\d+)\([^)]*\) host_pages=(\d+) gc_pages=(\d+) WAF=([\d.]+)$',read('summary.txt'),re.M)}
require(set(summary)==set(slots),'exact preregistered summaryslots; aliases excluded')
phases=[];last_end=None;last_counter=a
for slot,name in zip(slots,names):
 start,end=ts(f'phase-{slot}-start.time'),ts(f'phase-{slot}-end.time')
 require(end-start>=secs-2 and (last_end is None or start>=last_end),slot+' duration/order');last_end=end
 c0,c1=cnt(f'phase-{slot}-start.txt'),cnt(f'phase-{slot}-end.txt')
 require(c0['active']==c1['active']==1 and c0['epoch']==c1['epoch']==a['epoch'],slot+' epoch/active')
 require(all(c0[k]>=last_counter[k] for k in fields),slot+' counters rolled back')
 d={k:c1[k]-c0[k] for k in fields};require(d['host_bytes']>0 and d['host_pages']>0 and d['gc_pages']>=0,slot+' counter delta');last_counter=c1
 waf=1+d['gc_pages']/d['host_pages'];h,g,w=summary[slot]
 require(h==d['host_pages'] and g==d['gc_pages'] and abs(w-waf)<0.00000051,slot+' summary mismatch')
 detail={}
 if name=='FIO-Fast':
  jobs=fio(f'phase-{slot}.json',sum(expected.values()))
  require(len(jobs)==3 and {j['jobname'] for j in jobs}==set(expected),slot+' fio jobs')
  require(all(j['write']['io_bytes']==expected[j['jobname']] and j['write']['runtime']>=(secs-2)*1000 for j in jobs),slot+' fio duration/bytes')
  require(all((str(j['job options']['offset']),str(j['job options']['size']))==regions[j['jobname']] for j in jobs),slot+' fio regions')
 else:
  text=read(f'filebench-{slot}.txt')
  require(not re.search(r'ENOSPC|No space left on device|IO error|Failed to',text,re.I),slot+' Filebench errors')
  starts=re.findall(r'^([\d.]+): Running\.\.\.$',text,re.M);ends=re.findall(r'^([\d.]+): IO Summary:',text,re.M)
  n,rt=(2,secs//2) if name=='OLTP' else (1,secs)
  require(len(starts)==len(ends)==n,slot+' Filebench completions')
  times=[float(e)-float(s) for s,e in zip(starts,ends)];require(all(rt<=t<rt+60 for t in times),slot+' Filebench duration')
  detail={'process_runtimes_seconds':times}
 phases.append(dict(slot=slot,workload=name,actual_seconds=end-start,waf=waf,**d,**detail))
require(all(b[k]>=last_counter[k] for k in fields),'final counters rolled back')
series=[]
for l in read('control-series.txt').splitlines():
 k={a:int(v) for a,v in re.findall(r'\b(epoch|active|host_bytes|host_pages|gc_pages)=(\d+)',l)}
 if len(k)!=5 or not l.split()[0].isdigit():continue
 stamp=int(l.split()[0]);which=[s for s in slots if ts(f'phase-{s}-start.time')<=stamp]
 series.append(dict(unix_timestamp=stamp,phase=which[-1] if which else 'preparation',**k,cumulative_waf=1+k['gc_pages']/k['host_pages'] if k['active'] and k['host_pages'] else ''))
require(series,'missing30sseries')
series_output=P/'series'/f'{policy}.csv';series_output.parent.mkdir(exist_ok=True)
with series_output.open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(series[0]));w.writeheader();w.writerows(series)
print(json.dumps(dict(status='validated_saved_evidence',policy=policy,stage=stage,waf=1+b['gc_pages']/b['host_pages'],host_bytes=b['host_bytes'],host_pages=b['host_pages'],gc_pages=b['gc_pages'],actual_measured_seconds=ts(f'phase-{slots[-1]}-end.time')-ts(f'phase-{slots[0]}-start.time'),phases=phases,sample_rows=len(series),transition_count=len(slots)-1,measurement='manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement'),indent=2))
