"""Step journal and strict smoke gate invoked by the supplied entrypoint."""
from pathlib import Path
from datetime import datetime
import sys,json,hashlib,subprocess,csv,re,shutil
P=Path(__file__).resolve().parent;R=P.parents[1];action=sys.argv[1]
def now():return datetime.now().astimezone().isoformat()
def journal(note):
 for f in [P/'journal.md',R/'EXPERIMENT_LOG.md']:
  with f.open('a') as stream:stream.write('\n- '+now()+' '+P.name+' '+note+'\n')
if action=='build':
 m=json.loads((P/'metadata.json').read_text());mod=Path(m['module_path'])
 m['module_sha256']=hashlib.sha256(mod.read_bytes()).hexdigest();m['built_at']=now()
 require_kernel=subprocess.check_output(['modinfo','-F','vermagic',str(mod)],text=True).split()[0]
 assert require_kernel==m['kernel'],'module kernel mismatch'
 (P/'metadata.json').write_text(json.dumps(m,indent=2)+'\n')
 shutil.copy2(R/'buildoutput/build-online-v6.log',P/'build-online-v6.log')
 (P/'module-info.txt').write_text(subprocess.check_output(['modinfo',str(mod)],text=True))
 (P/'build-commands.txt').write_text('make -C /lib/modules/'+m['kernel']+'/build M=/home/oy/iCAT/online-v6-src -j$(nproc) NVMEVIRT_GC_POLICY=WATGC_V2 modules\n')
 commands=P/'compiler-commands';commands.mkdir(exist_ok=True)
 for f in (R/'online-v6-src').rglob('.*.cmd'):
  target=commands/f.relative_to(R/'online-v6-src');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
 journal('BUILD complete; moduleSHA='+m['module_sha256']);raise SystemExit(0)
stage=sys.argv[2];D=P/('mixT-onlinev6-rep1-smoke' if stage=='smoke' else 'mixT-onlinev6-rep1')
if action=='pre':
 if stage=='long':
  prev=json.loads((P/'smoke-result.json').read_text());assert prev['status']=='validated_saved_evidence','Smoke gate failed'
 assert not D.exists(),'Refuse overwrite'
 (P/'current-stage.txt').write_text(stage+'\n');(P/'status.txt').write_text('running_'+stage+'\n')
 journal('START '+stage+' PH_SECS='+('120' if stage=='smoke' else '4000')+'; raw='+str(D));raise SystemExit(0)
assert action=='post'
fields=['unix_timestamp','iso_time','elapsed_measured_seconds','phase','epoch','active','host_bytes','host_pages','gc_pages','cumulative_waf','sample_status','source']
starts=[]
for slot in 'ABCDEFGHI':
 f=D/f'phase-{slot}-start.time'
 if f.exists():starts.append((datetime.fromisoformat(f.read_text().strip()).timestamp(),slot))
with (D/'waf-series.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for line in (D/'control-series.txt').read_text().splitlines():
  words=line.split()
  if not words or not words[0].isdigit():continue
  ts=int(words[0]);k={a:int(b) for a,b in re.findall(r'\b(epoch|active|host_bytes|host_pages|gc_pages)=(\d+)',line)}
  good=k.get('active')==1 and k.get('host_pages',0)>0;ph=[x for x in starts if x[0]<=ts]
  w.writerow(dict(unix_timestamp=ts,iso_time=datetime.fromtimestamp(ts).astimezone().isoformat(),elapsed_measured_seconds=ts-starts[0][0] if starts else '',phase=max(ph)[1] if ph else 'preparation',cumulative_waf=1+k['gc_pages']/k['host_pages'] if good else '',sample_status='active_cumulative' if good else 'inactive_or_zero',source=str(D/'control-series.txt'),**k))
result=subprocess.run(['python3',str(P/'validate-results.py'),stage],capture_output=True,text=True)
(P/f'{stage}-validation.stdout.txt').write_text(result.stdout);(P/f'{stage}-validation.stderr.txt').write_text(result.stderr)
r={'stage':stage,'finished_at':now(),'raw_path':str(D),'status':'validated_saved_evidence' if result.returncode==0 else 'failed_validation','validation_exit':result.returncode}
if result.returncode==0:r.update(json.loads(result.stdout))
else:r['issue']=result.stderr[-2000:]
(P/f'{stage}-result.json').write_text(json.dumps(r,indent=2)+'\n');journal('FINISHED '+stage+' '+json.dumps(r))
if result.returncode:
 (P/'status.txt').write_text('STOPPED_'+stage+'_validation_failed\n')
raise SystemExit(result.returncode)
