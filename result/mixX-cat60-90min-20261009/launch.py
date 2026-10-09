#!/usr/bin/env python3
"""One sequential, stop-on-failure sweep; no automatic retries or overwrites."""
if __name__!='__main__':raise ImportError('Explicit launch only')
from pathlib import Path
from datetime import datetime
import os,sys,time,json,hashlib,subprocess,fcntl,traceback
P=Path(__file__).resolve().parent;R=P.parents[1]
meta=json.loads((P/'metadata.json').read_text())
def now():return datetime.now().astimezone().isoformat()
def status(s):(P/'status.txt').write_text(s+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def journal(d):
    line='\n- CAT60 screen90 '+json.dumps(d,ensure_ascii=False)+'\n'
    for p in [P/'journal.md',R/'EXPERIMENT_LOG.md']:
        with p.open('a') as f:f.write(line)
def publish(label):
    with (P/f'publish-{label}.log').open('w') as f:
        rc=subprocess.call(['python3',str(P/'publish-results.py')],stdout=f,stderr=subprocess.STDOUT,cwd=R)
    (P/f'publish-{label}.exit').write_text(str(rc)+'\n')
    return rc
campaign=(P/'campaign.lock').open('w');fcntl.flock(campaign,fcntl.LOCK_EX|fcntl.LOCK_NB)
shared=(R/'result/mix-20260911/device.lock').open('w')
status('waiting_for_exclusive_virtual_device_lock');fcntl.flock(shared,fcntl.LOCK_EX)
issues=[];exit_code=1;completed=[];current=None
try:
    for n,h in meta['execution_sha256'].items():assert sha(P/n)==h,'Changed execution input '+n
    for n,h in meta['workload_sha256'].items():assert sha(R/n)==h,'Changed workload '+n
    assert os.uname().release==meta['kernel'],'Kernel changed'
    assert not Path('/sys/module/nvmev').exists(),'Module in use'
    assert subprocess.run(['mountpoint','-q',str(R/'mnt')]).returncode!=0,'Mount in use'
    for policy,m in meta['modules'].items():
        assert sha(Path(m['path']))==m['sha256'],'Changed module '+policy
        assert subprocess.check_output(['modinfo','-F','vermagic',m['path']],text=True).split()[0]==os.uname().release
        assert not (P/f'mixX-{policy}-rep1').exists(),'Refuse existing result '+policy
    save(P/'started.json',dict(started_at=now(),run_id=meta['run_id'],source_commit=meta['source_commit']))
    env=os.environ.copy()
    for k in ['SMOKE','MULT','VM_FILES','VM_RUN','VM_CHUNKS','YCSB_SECS','PRE_FIO','ICAT_ROOT','MNT_DIR','MIXV_FIO_GB','MIXV_RECORDS']:
        env.pop(k,None)
    env.update(DEV='/dev/nvme1n1',ICAT_ROOT=str(R),MNT_DIR=str(R/'mnt'),MIX_BASE=str(P),
               MIX_JOURNAL=str(P/'journal.md'),BASH_ENV=str(P/'safety-env.sh'),MIXX_LOCK_HELD='1',PH_SECS=str(meta['phase_seconds']))
    for policy in meta['policy_order']:
        current=policy
        (P/'current-stage.txt').write_text(policy+'\n')
        for n,h in meta['workload_sha256'].items():assert sha(R/n)==h,'Changed workload '+n
        assert sha(Path(meta['modules'][policy]['path']))==meta['modules'][policy]['sha256']
        assert not Path('/sys/module/nvmev').exists(),'Module occupied between runs'
        assert subprocess.run(['mountpoint','-q',str(R/'mnt')]).returncode!=0,'Mount occupied between runs'
        journal(dict(event='started',policy=policy,time=now(),module=meta['modules'][policy],phase_order=meta['phase_order'],phase_seconds=meta['phase_seconds']))
        raw=P/f'mixX-{policy}-rep1'
        with (P/f'{policy}.console.txt').open('x') as f:
            proc=subprocess.Popen(['bash',str(P/'execution-mix.sh'),'mixX',policy,'1'],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
            (P/'pipeline.pid').write_text(str(proc.pid)+'\n')
            while proc.poll() is None:
                slots=[s for s in meta['phase_slots'] if (raw/f'phase-{s}-start.time').exists()]
                status('running_'+policy+'_'+(slots[-1] if slots else 'preparation'))
                time.sleep(3)
            rc=proc.wait()
        d=dict(policy=policy,finished_at=now(),runner_exit=rc,status='failed_run_preserved',raw_path=str(raw))
        if rc==0:
            v=subprocess.run(['python3',str(P/'validate-results.py'),policy],text=True,capture_output=True)
            (P/f'{policy}-validation.stdout.txt').write_text(v.stdout)
            (P/f'{policy}-validation.stderr.txt').write_text(v.stderr)
            d.update(validation_exit=v.returncode,status='failed_validation_preserved')
            if v.returncode==0:d.update(json.loads(v.stdout))
            rc=v.returncode
        save(P/f'{policy}-result.json',d);journal(dict(event='finished',**d))
        subprocess.run(['python3',str(P/'rank-results.py')],check=True,cwd=R)
        if rc:
            exit_code=rc;issues.append(policy+' failed; no subsequent arm executed');break
        completed.append(policy)
        status('validated_'+policy+'_publishing')
        if publish(policy):
            exit_code=1;issues.append(policy+' publication failed; remaining queue stopped');break
    else:exit_code=0
except Exception:
    issues.append(traceback.format_exc());(P/'launcher-error.txt').write_text(issues[-1])
result=dict(run_id=meta['run_id'],status='validated_all60' if not issues and len(completed)==60 else 'failed_or_incomplete_preserved',
            exit_code=exit_code,completed_count=len(completed),completed=completed,current_policy=current,issues=issues,finished_at=now(),raw_path=str(P))
save(P/'result.json',result);status(result['status']);journal(result)
with (P/'report.md').open('a') as f:f.write('\nCampaign outcome: '+json.dumps(result,ensure_ascii=False)+'\n')
subprocess.run(['python3',str(P/'rank-results.py')],check=False,cwd=R)
pub=publish('final')
subprocess.run(['notify-send','iCAT CAT60 90min',result['status']],check=False)
raise SystemExit(exit_code or pub)
