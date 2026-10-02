import subprocess,fcntl,re,time
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1];Q=ROOT/'result/queue33-icat2-20261002-r2'
def journal(s):
 with (P/'journal.md').open('a') as f:f.write('\n- '+time.strftime('%Y-%m-%d %H:%M:%S')+' '+s+'\n')
assert not Path('/sys/module/nvmev').exists(),'Module occupied; do not reset another run'
assert subprocess.run(['mountpoint','-q',str(ROOT/'mnt')]).returncode!=0,'Mount occupied'
with (ROOT/'result/mix-20260911/device.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 (P/'status.txt').write_text('validation_running\n');journal('START repaired validation; module safety and shared lock preserved')
 with (P/'validation.console.txt').open('w') as log:rc=subprocess.call(['bash',str(ROOT/'script/validate-new-machine.sh')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
(P/'validation.exit').write_text(str(rc)+'\n')
t=(P/'validation.console.txt').read_text();m=re.search(r'^Evidence: (\S+)',t,re.M)
if m:(P/'validation-path.txt').write_text(m[1]+'\n')
last=t.strip().splitlines()[-1] if t.strip() else ''
if rc or last!='PASS':
 (P/'status.txt').write_text('validation_FAILED_queue_NOT_started\n');journal('FAIL; stop full sweep and publish only failure evidence icat-2')
 with (P/'publish.log').open('a') as f:pc=subprocess.call(['python3',str(Q/'publish.py'),'repaired validation FAILED; no sweep started'],stdout=f,stderr=subprocess.STDOUT)
 (P/'publish.exit').write_text(str(pc)+'\n');raise SystemExit(rc or 1)
(P/'status.txt').write_text('validation_PASS_queue33_running\n');journal('PASS3policy gate; START fixed-only11x60; do not infer all60/manual equivalence')
rc=subprocess.call(['python3',str(Q/'run-fixed-campaign.py')],cwd=ROOT)
(P/'queue33.exit').write_text(str(rc)+'\n');(P/'status.txt').write_text('queue33_finished_exit'+str(rc)+'\n');journal('QUEUE33 exit='+str(rc))
