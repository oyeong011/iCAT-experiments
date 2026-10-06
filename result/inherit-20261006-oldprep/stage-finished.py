from pathlib import Path
from datetime import datetime
import sys,subprocess,json
P=Path(__file__).resolve().parent;R=P.parents[1];policy,stage=sys.argv[1:]
v=subprocess.run(['python3',str(P/'validate-results.py'),policy,stage],capture_output=True,text=True)
(P/f'{policy}-{stage}-validation.stdout.txt').write_text(v.stdout)
(P/f'{policy}-{stage}-validation.stderr.txt').write_text(v.stderr)
result=dict(policy=policy,stage=stage,finished_at=datetime.now().astimezone().isoformat(),validation_exit=v.returncode,status='failed_validation_preserved')
if v.returncode==0:result.update(json.loads(v.stdout))
(P/f'{policy}-{stage}-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
line='\n- mixV '+policy+' '+stage+' finished '+json.dumps(result,ensure_ascii=False)+'\n'
for f in [P/'journal.md',R/'EXPERIMENT_LOG.md']:
 with f.open('a') as out:out.write(line)
if v.returncode:raise SystemExit(v.returncode)
rc=subprocess.call(['python3',str(P/'publish-results.py')]);(P/f'{policy}-{stage}-publish.exit').write_text(str(rc)+'\n')
raise SystemExit(rc)
