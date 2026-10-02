import json,os,signal,time,subprocess,re,csv
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1];N=ROOT/'result/queue33-icat2-20261002'
t=json.loads((P/'transition.json').read_text());parent=t['old_queue_pid'];child=t['current_runner_pid']
def journal(s):
 with (P/'journal.md').open('a') as f:f.write('\n- '+time.strftime('%Y-%m-%d %H:%M:%S')+' '+s+'\n')
(P/'status.txt').write_text('waiting_for_current_run_to_finish\n')
while True:
 try:
  stat=Path(f'/proc/{child}/stat').read_text();state=stat[stat.rfind(')')+2:].split()[0]
  if state=='Z':break
 except FileNotFoundError:break
 time.sleep(10)
# Runner has completed and cleaned up; terminate ONLY the frozen queue parent.
try:os.kill(parent,signal.SIGTERM);os.kill(parent,signal.SIGCONT)
except ProcessLookupError:pass
for _ in range(30):
 if not Path(f'/proc/{parent}').exists():break
 time.sleep(1)
assert not Path('/sys/module/nvmev').exists(),'Existing run did not clean up; refuse validation'
assert subprocess.run(['mountpoint','-q',str(ROOT/'mnt')]).returncode!=0,'Mount still busy'
old=ROOT/'result/mixed-cat-full-20261002/mixD-onlinev4-rep1'
journal('Old queue stopped at normal completed-run boundary; current run preserved '+str(old))
(P/'status.txt').write_text('validation_running\n');journal('Validation START arm47/arm50/gh-greedy; no QUEUE33 measurement before PASS.')
with (P/'validation.console.txt').open('w') as log:
 rc=subprocess.call(['bash',str(ROOT/'script/validate-new-machine.sh')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
(P/'validation.exit').write_text(str(rc)+'\n')
text=(P/'validation.console.txt').read_text();m=re.search(r'^Evidence: (\S+)',text,re.M)
if m:(P/'validation-path.txt').write_text(m[1]+'\n')
last=text.strip().splitlines()[-1] if text.strip() else ''
if rc!=0 or last!='PASS':
 (P/'status.txt').write_text('validation_FAILED_queue_NOT_started\n');journal('Validation FAILED exit='+str(rc)+'; fixed queue NOT started; publish evidence icat-2 only.')
 with (P/'publish.log').open('a') as log:prc=subprocess.call(['python3',str(N/'publish.py'),'handoff validation FAILED; queue not started'],stdout=log,stderr=subprocess.STDOUT)
 (P/'publish.exit').write_text(str(prc)+'\n')
 raise SystemExit(rc or 1)
journal('Validation PASS; three-policy tolerance gate only, NOT equivalence of all60/manualmeasurement. Host cohorts remain separate.')
(P/'status.txt').write_text('validation_PASS_queue33_running\n')
# Run fixed-only queue within this persistent service. No reboot/source/module edits.
rc=subprocess.call(['python3',str(N/'run-fixed-campaign.py')],cwd=ROOT)
(P/'queue33.exit').write_text(str(rc)+'\n');(P/'status.txt').write_text('queue33_finished_exit'+str(rc)+'\n');journal('QUEUE33 exit='+str(rc))
