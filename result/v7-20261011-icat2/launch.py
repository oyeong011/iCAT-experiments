"""One-shot CAT60-gated v7 queue; no device operations before completion/push gate."""
from pathlib import Path
from datetime import datetime
import subprocess,os,json,time,hashlib,fcntl,traceback
from prepare import gate,prepare
from analyze import analyze
from report import refresh
P=Path(__file__).resolve().parent;R=P.parents[1];M=json.loads((P/'metadata.json').read_text())
def now():return datetime.now().astimezone().isoformat()
def save(p,d):
    t=Path(str(p)+'.tmp');t.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def status(s):
    (P/'status.txt').write_text(s+'\n')
def journal(d):
    for p in [P/'journal.md',R/'EXPERIMENT_LOG.md']:
        with p.open('a') as f:f.write('\n- v7 icat-2 '+json.dumps(d,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def service_done():
    proc=subprocess.run(['systemctl','--user','show',M['cat_service'],'--property=MainPID','--property=LoadState','--property=ActiveState'],text=True,capture_output=True)
    fields=dict(line.split('=',1) for line in proc.stdout.splitlines() if '=' in line)
    return fields.get('LoadState')=='not-found' or (fields.get('MainPID')=='0' and fields.get('ActiveState') not in ('active','activating','deactivating'))
def idle():
    assert not Path('/sys/module/nvmev').exists(),'NVMeVirt occupied / cleanup failed'
    assert subprocess.run(['mountpoint','-q',str(R/'mnt')]).returncode!=0,'mount occupied / cleanup failed'
def verify_inputs():
    assert os.uname().release==M['kernel'],'kernel changed'
    assert Path('/etc/machine-id').read_text().strip()==M['machine_id'],'wrong machine'
    for n,h in M['workload_sha256'].items():assert sha(R/n)==h,'changed workload '+n
    for n,h in M['input_sha256'].items():assert sha(P/n)==h,'changed saved input '+n
    for n,h in M['automation_sha256'].items():assert sha(P/n)==h,'changed automation '+n
    assert sha(Path(M['module_path']))==M['module_sha256'],'module hash changed'
    assert subprocess.check_output(['modinfo','-F','vermagic',M['module_path']],text=True).strip()==M['vermagic']
def publish(label):
    for attempt in range(1,4):
        with (P/f'publish-{label}-{attempt}.log').open('x') as f:
            try:rc=subprocess.call(['python3',str(P/'publish.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT)
            except Exception:traceback.print_exc(file=f);rc=1
        (P/f'publish-{label}-{attempt}.exit').write_text(str(rc)+'\n')
        if rc==0:return 0
        time.sleep(15)
    journal(dict(event='push_failed_after_retries',label=label,time=now()));return rc

def main():
    single=(P/'queue.lock').open('a');fcntl.flock(single,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (P/'started.json').exists(),'one-shot queue refuses automatic replay'
    status('waiting_for_CAT60_arm29_and_final_push');refresh()
    while not (gate() and service_done()):
        time.sleep(30)
    status('waiting_for_exclusive_device_lock')
    shared=(R/'result/mix-20260911/device.lock').open('a');fcntl.flock(shared,fcntl.LOCK_EX)
    assert gate() and service_done(),'completion gate changed'
    verify_inputs();idle();os.environ['MIXX_LOCK_HELD']='1'
    runner_hashes=prepare()
    save(P/'started.json',dict(time=now(),cat_completion=json.loads((Path(M['cat_resume'])/'result.json').read_text()),runner_sha256=runner_hashes))
    journal(dict(event='queue_started_after_CAT60',time=now(),runner_sha256=runner_hashes))
    published=[];outcomes=[]
    if publish('prereg')!=0:published.append('prereg')
    for stage,label,seq in [('fvo90','mixX','F V O'),('mixY','mixY',M['mixY_sequence'])]:
        verify_inputs();idle()
        for n,h in runner_hashes.items():assert sha(P/n)==h,'changed prepared runner '+n
        raw=P/stage/f'{label}-onlinev7-rep1';assert not raw.exists(),'refuse overwrite '+str(raw)
        env=os.environ.copy()
        for k in ['SMOKE','MULT','VM_FILES','VM_RUN','VM_CHUNKS','YCSB_SECS','PRE_FIO','MIXV_FIO_GB','MIXV_RECORDS','MIXY_SEQ']:
            env.pop(k,None)
        env.update(PH_SECS='1800',MIXY_SEQ=seq,MIX_BASE=str(P/stage),MIX_JOURNAL=str(P/'journal.md'),BASH_ENV=str(P/'safety-env.sh'),MIXX_LOCK_HELD='1',DEV='/dev/nvme1n1',ICAT_ROOT=str(R),MNT_DIR=str(R/'mnt'))
        cmd=['bash',str(P/'execution-v7.sh'),label,'onlinev7','1']
        journal(dict(event='experiment_started',time=now(),stage=stage,command=cmd,sequence=seq,module_sha256=M['module_sha256'],raw_path=str(raw)))
        with (P/f'{stage}.console.txt').open('x') as f:
            proc=subprocess.Popen(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
            (P/'pipeline.pid').write_text(str(proc.pid)+'\n')
            while proc.poll() is None:
                slots=sorted(raw.glob('phase-S*-start.time'));current=slots[-1].name.split('-')[1] if slots else 'preparation'
                status('running_'+stage+'_'+current);time.sleep(3)
            rc=proc.wait()
        try:d=analyze(stage,raw,seq.split(),rc)
        except Exception:
            d=dict(stage=stage,status='failed_preserved',runner_exit=rc,issues=['analyzer crashed: '+traceback.format_exc()],raw_path=str(raw))
            save(P/f'{stage}-result.json',d)
        cleanup_error=None
        try:idle()
        except AssertionError as e:
            cleanup_error=str(e);d['issues'].append(cleanup_error);d['status']='failed_preserved';save(P/f'{stage}-result.json',d)
        outcomes.append(dict(stage=stage,status=d['status']))
        if d['status']!='validated_saved_evidence':
            with (P/'failures.tsv').open('a') as f:f.write('\t'.join([now(),stage,str(rc),json.dumps(d['issues'],ensure_ascii=False),str(raw)])+'\n')
        journal(dict(event='experiment_finished',time=now(),stage=stage,status=d['status'],runner_exit=rc,waf=d.get('waf'),issues=d['issues'],raw_path=str(raw)))
        status('publishing_'+stage);refresh()
        if publish(stage):published.append(stage)
        if cleanup_error:raise RuntimeError('Cannot safely continue: '+cleanup_error)
    outcome='completed_with_failures' if any(x['status']!='validated_saved_evidence' for x in outcomes) else 'completed'
    save(P/'result.json',dict(status=outcome,finished_at=now(),experiments=outcomes,push_failures=published))
    status(outcome);journal(dict(event='queue_finished',time=now(),status=outcome,push_failures=published));refresh()
    if publish('final'):status(outcome+'_final_push_failed');refresh();return 1
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:
        error=traceback.format_exc();(P/'launcher-error.txt').write_text(error);status('halted_safely');journal(dict(event='launcher_halted',time=now(),error=error));refresh();raise
