import re,sys,gzip,json
from pathlib import Path
d=Path(sys.argv[1]);records=int(sys.argv[2]);ops=int(sys.argv[3]);vmrun=int(sys.argv[4])
for p in d.glob('ycsb-*.txt*'):
 if p.name=='ycsb-run.txt' or p.name=='ycsb-run.txt.gz':continue
 t=gzip.open(p,'rt').read() if p.suffix=='.gz' else p.read_text()
 counts=[(name,int(n)) for name,n in re.findall(r'^\[(INSERT|UPDATE|READ|SCAN|DELETE|READ-MODIFY-WRITE)\], Operations, (\d+)',t,re.M)]
 got=sum(n for name,n in counts);want=records if 'load' in p.name else ops
 if got!=want:raise SystemExit(f'{p.name}: completed{got},requested{want}')
 errors=[(name,status,int(n)) for name,status,n in re.findall(r'^\[(\S+)\], Return=([^,]+), (\d+)',t,re.M) if status!='OK' and int(n)>0]
 if errors:raise SystemExit(f'{p.name}: {errors}')
for p in d.glob('filebench-*.txt'):
 t=p.read_text();m=re.search(r'IO Summary:.*? ([\d.]+)s$',t,re.M)
 if 'IO Summary' not in t:raise SystemExit('missing filebench summary:'+str(p))
 # Profile is the requested duration; IO Summary rounding need not equal integer.
 if not any(re.search(r'^run '+str(vmrun)+r'$',f.read_text(),re.M) for f in d.glob('*.f')):raise SystemExit('profile requested duration mismatch')
(d/'application-validation.json').write_text(json.dumps({'status':'passed','YCSB_requested_ops':ops,'YCSB_requested_records':records,'filebench_requested_seconds':vmrun})+'\n')
