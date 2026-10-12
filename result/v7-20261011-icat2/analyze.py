"""Read-only, per-run evidence validation; failed results retain diagnostic WAF."""
from pathlib import Path
from datetime import datetime
import re,json,csv,gzip
P=Path(__file__).resolve().parent
NAMES={'F':'FIO-Fast','S':'FIO-Slow','V':'Varmail','O':'OLTP'}
def writecsv(path,rows,fields):
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def sample_counts(text):
    counts={};active=None;starts={};ends={};outside={};bad=[];seen=set();duplicates=0
    for line in text.splitlines():
        if line in seen:duplicates+=1;continue
        seen.add(line)
        m=re.search(r'mix-mix[XY]-onlinev7-\d+ phase=(S\d+) (START|END)\b',line)
        if m:
            s,e=m.groups()
            if e=='START':
                if active:bad.append('overlapping marker '+active+' '+s)
                starts[s]=starts.get(s,0)+1;active=s
            else:
                if active!=s:bad.append('unmatched END '+s)
                ends[s]=ends.get(s,0)+1;active=None
        m=re.search(r'WATGC_V2 sample .*?ns=(\d+) part=(\d+)\b',line)
        if m:
            ns,part=map(int,m.groups());key=(active,ns,part)
            counts[key]=counts.get(key,0)+1
    if active:bad.append('missing END '+active)
    return counts,starts,ends,bad,duplicates

def analyze(stage,raw,sequence,runner_exit):
    raw=Path(raw);issues=[];warnings=[];phases=[];series=[]
    def require(ok,msg):
        if not ok:issues.append(msg)
    def read(n):
        f=raw/n
        if f.exists():return f.read_text(errors='replace')
        if Path(str(f)+'.gz').exists():
            with gzip.open(str(f)+'.gz','rt',errors='replace') as x:return x.read()
        raise FileNotFoundError(n)
    def cnt(n):return {k:int(v) for k,v in re.findall(r'\b(epoch|active|host_bytes|host_pages|gc_pages)=(\d+)',read(n).splitlines()[0])}
    def ts(n):return datetime.fromisoformat(read(n).strip()).timestamp()
    def attempt(name,fn):
        try:return fn()
        except Exception as e:issues.append(name+': '+type(e).__name__+': '+str(e));return None
    def fio(n,wanted):
        jobs=json.loads(read(n))['jobs'];require(bool(jobs) and all(j['error']==0 for j in jobs),n+' fio error')
        require(sum(j['write']['io_bytes'] for j in jobs)==wanted,n+' requested IO incomplete');return jobs
    m=json.loads((P/'metadata.json').read_text());slots=[f'S{i:02}' for i in range(1,len(sequence)+1)];fields=['host_bytes','host_pages','gc_pages']
    require(runner_exit==0,'runner exited '+str(runner_exit))
    attempt('exit-code',lambda:require(read('exit-code.txt').strip()==str(runner_exit),'exit-code disagreement'))
    a=attempt('started',lambda:cnt('started.txt'));b=attempt('stopped',lambda:cnt('stopped.txt'))
    z=attempt('final-control',lambda:cnt('final-control.txt'));p=attempt('prepared',lambda:cnt('prepared.txt'))
    if a:require(a['active']==1 and all(a[k]==0 for k in fields),'nonzero start')
    if p:require(p['active']==0 and all(p[k]==0 for k in fields),'prep included in measurement')
    if a and b:
        require(b==z and b['active']==0 and b['epoch']==a['epoch'] and b['host_pages']>0 and b['gc_pages']>0,'final counters or cleanup snapshot invalid')
    def parts():
        x=[dict((k,int(v)) for k,v in re.findall(r'(part|host_pages|gc_pages|arm)=(\d+)',l)) for l in read('stopped.txt').splitlines()[1:] if l.startswith('part=')]
        require({v['part'] for v in x}==set(range(4)) and len(x)==4,'partition set')
        require(all(sum(v[k] for v in x)==b[k] for k in ['host_pages','gc_pages']),'partition sum')
    if b:attempt('partitions',parts)
    byte_difference=None
    def bytecheck():
        before=int(read('block-stat-before.txt'));after=int(read('block-stat-after.txt'))
        require(after==int(read('block-stat-stop-before.txt')),'writes crossed stop boundary')
        difference=b['host_bytes']-(after-before)*512;require(difference==0,'host_bytes vs block-stat mismatch '+str(difference));return difference
    if b:byte_difference=attempt('block statistics',bytecheck)
    attempt('preset',lambda:fio('preset.json',6*1024**3));attempt('prepare',lambda:fio('prepare.json',3*1024**3))
    environment=attempt('environment',lambda:read('environment.txt'))
    if environment:require(m['module_sha256'] in environment and m['kernel'] in environment,'module hash/kernel provenance mismatch')
    device=attempt('device',lambda:read('device.txt'))
    if device:require('CSL_Virt' in device,'unverified virtual model')
    file_inodes=set();last=a;last_end=None
    summary=attempt('summary',lambda:read('summary.txt'))
    summary_rows={} if not summary else {s:(int(h),int(g),float(w)) for s,h,g,w in re.findall(r'^phase(S\d+)\([^)]*\) host_pages=(\d+) gc_pages=(\d+) WAF=([\d.]+)$',summary,re.M)}
    if summary:require(set(summary_rows)==set(slots),'summary phase coverage')
    for slot,kind in zip(slots,sequence):
        def phase():
            nonlocal last,last_end
            start,end=ts(f'phase-{slot}-start.time'),ts(f'phase-{slot}-end.time')
            require(end-start>=1798 and (last_end is None or start>=last_end),slot+' duration/order');last_end=end
            c0,c1=cnt(f'phase-{slot}-start.txt'),cnt(f'phase-{slot}-end.txt')
            require(c0['active']==c1['active']==1 and a and c0['epoch']==c1['epoch']==a['epoch'],slot+' epoch/active')
            if last:require(all(c0[k]>=last[k] for k in fields),slot+' counter rollback')
            d={k:c1[k]-c0[k] for k in fields};last=c1
            require(d['host_pages']>0 and d['host_bytes']>0 and d['gc_pages']>=0,slot+' invalid delta')
            waf=1+d['gc_pages']/d['host_pages'] if d['host_pages']>0 else None
            phases.append(dict(slot=slot,workload=NAMES[kind],actual_seconds=end-start,waf=waf,**d,source=str(raw/f'phase-{slot}-end.txt')))
            if slot in summary_rows:
                h,g,w=summary_rows[slot];require(h==d['host_pages'] and g==d['gc_pages'] and waf is not None and abs(w-waf)<0.00000051,slot+' summary mismatch')
            inode,size=read(f'fio-file-{slot}-start.stat').split();file_inodes.add(inode);require(int(size)==6*1024**3,slot+' kept file size')
            if kind in 'FS':
                divisor=600 if kind=='F' else 2400
                expected={k:n*1800//divisor for k,n in [('hot',58982400000),('warm',29491200000),('cold',9830400000)]}
                jobs=fio(f'phase-{slot}.json',sum(expected.values()))
                require(len(jobs)==3 and {j['jobname'] for j in jobs}==set(expected),slot+' FIO job coverage')
                regions={'hot':('0','512M'),'warm':('512M','1536M'),'cold':('2G','4G')}
                for j in jobs:
                    n=j['jobname'];opts=j['job options'];require(j['write']['io_bytes']==expected[n] and j['write']['runtime']>=1798000,slot+' job completion/time')
                    require((str(opts['offset']),str(opts['size']))==regions[n],slot+' FIO region')
                    require(int(opts['randseed'])==m['seeds'][n],slot+' FIO seed')
            else:
                text=read(f'filebench-{slot}.txt');require(not re.search(r'ENOSPC|No space left on device|IO error|Failed to',text,re.I),slot+' Filebench error')
                starts=re.findall(r'^([\d.]+): Running\.\.\.$',text,re.M);ends=re.findall(r'^([\d.]+): IO Summary:',text,re.M)
                n,rt=(2,900) if kind=='O' else (1,1800)
                require(len(starts)==len(ends)==n,slot+' Filebench chunks incomplete')
                require(all(rt<=float(e)-float(s)<rt+60 for s,e in zip(starts,ends)),slot+' Filebench chunk runtime')
        attempt(slot,phase)
    require(len(phases)==len(sequence),'incomplete phase counters');require(len(file_inodes)==1,'6GiB file was not kept')
    require(not list(raw.glob('phase-*-create.json')),'unexpected FIO recreation')
    if b and last:require(all(b[k]>=last[k] for k in fields),'final counter rollback')
    kernel=attempt('kernel log',lambda:read('kernel.log')) or ''
    counts,starts,ends,marker_issues,duplicates=sample_counts(kernel);issues.extend(marker_issues)
    samples=[]
    for slot,kind in zip(slots,sequence):
        require(starts.get(slot)==ends.get(slot)==1,slot+' missing/duplicate kernel phase markers')
        for part in range(4):samples.append(dict(slot=slot,workload=NAMES[kind],namespace=0,partition=part,sample_lines=counts.get((slot,0,part),0)))
    for (slot,ns,part),n in counts.items():
        if slot not in slots or ns!=0 or part not in range(4):samples.append(dict(slot=slot or 'outside_phase',workload='unassigned',namespace=ns,partition=part,sample_lines=n))
    require(all(sum(n for (slot,ns,p),n in counts.items() if ns==0 and p==part)>0 for part in range(4)),'missing online samples for a partition')
    if re.search(r'callbacks suppressed|messages? dropped|overrun',kernel,re.I):warnings.append('kernel log may contain dropped/suppressed messages; sample counts are observed lower bounds')
    def timeseries():
        for l in read('control-series.txt').splitlines():
            k={key:int(v) for key,v in re.findall(r'\b(epoch|active|host_bytes|host_pages|gc_pages)=(\d+)',l)}
            if len(k)!=5 or not l.split()[0].isdigit():continue
            series.append(dict(unix_timestamp=int(l.split()[0]),**k,cumulative_waf=1+k['gc_pages']/k['host_pages'] if k['active'] and k['host_pages'] else ''))
        require(bool(series),'missing 30sec series')
    attempt('series',timeseries)
    out=dict(stage=stage,status='validated_saved_evidence' if not issues else 'failed_preserved',runner_exit=runner_exit,raw_path=str(raw),
        finished_at=datetime.now().astimezone().isoformat(),issues=issues,warnings=warnings,waf=1+b['gc_pages']/b['host_pages'] if b and b.get('host_pages',0)>0 else None,
        host_bytes=b.get('host_bytes') if b else None,gc_pages=b.get('gc_pages') if b else None,host_bytes_minus_block_stat=byte_difference,
        phases=phases,sample_counts=samples,duplicate_kernel_lines_ignored=duplicates,series_rows=len(series),
        interpretation='WAF from manual FTL page counters; includes learning. Failed-run WAF is diagnostic only. Samples are observed log lines, not independent repetitions.')
    (P/f'{stage}-result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    writecsv(P/f'{stage}-phases.csv',phases,['slot','workload','actual_seconds','host_bytes','host_pages','gc_pages','waf','source'])
    writecsv(P/f'{stage}-samples.csv',samples,['slot','workload','namespace','partition','sample_lines'])
    writecsv(P/f'{stage}-series.csv',series,['unix_timestamp','epoch','active','host_bytes','host_pages','gc_pages','cumulative_waf'])
    return out
