"""Authorized one-time arm03 retry, then arm04..29; no raw overwrites."""
from pathlib import Path
from datetime import datetime
import os,sys,time,json,hashlib,subprocess,fcntl,traceback
from refresh import refresh
Q=Path(__file__).resolve().parent;P=Q.parent;R=P.parents[1]
meta=json.loads((Q/'metadata.json').read_text())
def now():return datetime.now().astimezone().isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def status(s):(Q/'status.txt').write_text(s+'\n')
def journal(d):
    for p in [Q/'journal.md',R/'EXPERIMENT_LOG.md']:
        with p.open('a') as f:f.write('\n- CAT60 continuation '+json.dumps(d,ensure_ascii=False)+'\n')
def publish(label):
    with (Q/f'publish-{label}.log').open('x') as f:
        rc=subprocess.call(['python3',str(P/'publish-results.py')],stdout=f,stderr=subprocess.STDOUT,cwd=R)
    (Q/f'publish-{label}.exit').write_text(str(rc)+'\n')
    return rc
def idle():
    assert not Path('/sys/module/nvmev').exists(),'NVMeVirt module occupied or cleanup failed'
    assert subprocess.run(['mountpoint','-q',str(R/'mnt')]).returncode!=0,'Virtual mount occupied or cleanup failed'
def inputs():
    for n,h in meta['execution_sha256'].items():assert sha(P/n)==h,'Changed original execution input '+n
    for n,h in meta['workload_sha256'].items():assert sha(R/n)==h,'Changed workload '+n
    for n,h in meta['continuation_sha256'].items():assert sha(Q/n)==h,'Changed continuation input '+n
    assert os.uname().release==meta['kernel'],'Kernel changed'
    assert Path('/etc/machine-id').read_text().strip()==meta['machine_id'],'Wrong machine'
def main():
    campaign=(P/'campaign.lock').open('a');fcntl.flock(campaign,fcntl.LOCK_EX|fcntl.LOCK_NB)
    shared=(R/'result/mix-20260911/device.lock').open('a');status('waiting_for_exclusive_virtual_device_lock')
    fcntl.flock(shared,fcntl.LOCK_EX)
    completed=[];failed=[];current=None;issues=[];exit_code=1
    try:
        inputs();idle()
        assert meta['policy_order']==[f'arm{n:02}' for n in range(3,30)],'Scope changed'
        for policy in meta['policy_order']:
            m=meta['modules'][policy]
            assert sha(Path(m['path']))==m['sha256'],'Changed module '+policy
            assert subprocess.check_output(['modinfo','-F','vermagic',m['path']],text=True).split()[0]==meta['kernel']
            assert not (Q/f'mixX-{policy}-rep1').exists(),'Refuse overwrite '+policy
        preservation=json.loads((Q/'original-preservation-sha256.json').read_text())
        for n,h in preservation.items():assert sha(P/n)==h,'Original evidence changed '+n
        save(Q/'started.json',dict(started_at=now(),policy_order=meta['policy_order'],run_id=meta['run_id']))
        env=os.environ.copy()
        for k in ['SMOKE','MULT','VM_FILES','VM_RUN','VM_CHUNKS','YCSB_SECS','PRE_FIO','ICAT_ROOT','MNT_DIR','MIXV_FIO_GB','MIXV_RECORDS']:
            env.pop(k,None)
        env.update(DEV='/dev/nvme1n1',ICAT_ROOT=str(R),MNT_DIR=str(R/'mnt'),MIX_BASE=str(Q),
                   MIX_JOURNAL=str(Q/'journal.md'),BASH_ENV=str(P/'safety-env.sh'),MIXX_LOCK_HELD='1',PH_SECS='1800')
        for policy in meta['policy_order']:
            current=policy;inputs();idle()
            assert sha(Path(meta['modules'][policy]['path']))==meta['modules'][policy]['sha256']
            raw=Q/f'mixX-{policy}-rep1';console=Q/f'{policy}.console.txt'
            journal(dict(event='started',time=now(),policy=policy,attempt='retry1' if policy=='arm03' else 'first',
                         raw_path=str(raw),module=meta['modules'][policy],phase_order=meta['phase_order'],phase_seconds=1800))
            with console.open('x') as f:
                proc=subprocess.Popen(['bash',str(P/'execution-mix.sh'),'mixX',policy,'1'],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
                (Q/'pipeline.pid').write_text(str(proc.pid)+'\n')
                while proc.poll() is None:
                    slots=[s for s in meta['phase_slots'] if (raw/f'phase-{s}-start.time').exists()]
                    status('running_'+policy+'_'+(slots[-1] if slots else 'preparation'));time.sleep(3)
                rc=proc.wait()
            d=dict(policy=policy,runner_exit=rc,finished_at=now(),raw_path=str(raw),status='failed_run_preserved')
            can_continue=False
            if rc in (0,1):
                validator='validate-results.py' if rc==0 else 'classify-byte-failure.py'
                args=['python3',str(Q/validator),policy,str(raw)]
                if rc==1:args.append(str(console))
                v=subprocess.run(args,text=True,capture_output=True,cwd=R)
                (Q/f'{policy}-validation.stdout.txt').write_text(v.stdout)
                (Q/f'{policy}-validation.stderr.txt').write_text(v.stderr)
                d['validation_exit']=v.returncode
                if v.returncode==0:
                    d.update(json.loads(v.stdout));can_continue=True
                elif rc==0:d['status']='failed_validation_preserved'
            try:idle()
            except AssertionError as e:d['cleanup_error']=str(e);can_continue=False
            if d['status']=='validated_saved_evidence':completed.append(policy)
            else:failed.append(policy)
            save(Q/f'{policy}-result.json',d);journal(dict(event='finished',**d));refresh()
            status(d['status']+'_'+policy+'_publishing')
            if publish(policy):issues.append(policy+' push failed');break
            if not can_continue:issues.append(policy+' unexpected failure; halted');break
        else:exit_code=0
    except Exception:
        issues.append(traceback.format_exc());(Q/'launcher-error.txt').write_text(issues[-1])
    outcome='completed_assignment_with_failures' if exit_code==0 and failed else 'completed_assignment' if exit_code==0 else 'halted'
    result=dict(run_id=meta['run_id'],status=outcome,exit_code=exit_code,completed=completed,failed=failed,
                current_policy=current,issues=issues,finished_at=now(),arm30_to_59='not_scheduled_on_this_host')
    save(Q/'result.json',result);status(outcome);journal(result);refresh()
    pub=publish('final')
    if pub:status(outcome+'_final_push_failed')
    return exit_code or pub
if __name__=='__main__':raise SystemExit(main())
