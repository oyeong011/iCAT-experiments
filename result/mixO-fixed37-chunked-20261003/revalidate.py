# Revalidate saved raw evidence only. Never launches workloads.
import json,re
from pathlib import Path
from datetime import datetime
P=Path(__file__).resolve().parent;ROOT=P.parents[1];D=P/'mixO-fixed37-rep1-x20'
result=json.loads((P/'before-revalidation-result.json').read_text())
rc=int((D/'exit-code.txt').read_text());issues=[]
assert rc==0, 'raw runner failed'
result['revalidated_at']=datetime.now().astimezone().isoformat()
result['correction']='Original validator expected seconds at end of IO Summary, but Filebench reports prefix timestamps. Validate Running-to-IO Summary durations for all 21 processes; original failure record retained.'
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
  rt=900 if slot=='A' else 18000
  n=20 if slot=='A' else 1
  assert re.search(r'^run '+str(rt)+r'$',(D/profile).read_text(),re.M),'profile duration'
  text=(D/f'filebench-{slot}.txt').read_text();assert 'IO Summary' in text,'Filebench completion'
  starts=re.findall(r'^([\d.]+): Running\.\.\.$',text,re.M)
  ends=re.findall(r'^([\d.]+): IO Summary:',text,re.M)
  assert len(starts)==len(ends)==n,'chunk count'
  durations=[float(e)-float(a) for a,e in zip(starts,ends)]
  assert all(rt<=x<rt+60 for x in durations),'all chunk runtimes'
  sec=(datetime.fromisoformat((D/f'phase-{slot}-end.time').read_text().strip())-datetime.fromisoformat((D/f'phase-{slot}-start.time').read_text().strip())).total_seconds()
  assert 18000<=sec<=19800,'actual phase duration'
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
print(json.dumps(result,indent=2))
assert not issues, issues
