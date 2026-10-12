"""Render runner only after CAT60's arm29 and final push; preview is syntax-only."""
from pathlib import Path
import json,subprocess,difflib,hashlib,os
P=Path(__file__).resolve().parent; R=P.parents[1]
def gate(q=None):
    q=Path(q) if q else Path(json.loads((P/'metadata.json').read_text())['cat_resume'])
    try:
        d=json.loads((q/'result.json').read_text())
        return (d['status'] in ('completed_assignment','completed_assignment_with_failures') and
                d['current_policy']=='arm29' and (q/'arm29-result.json').is_file() and
                (q/'publish-arm29.exit').read_text().strip()=='0' and
                (q/'publish-final.exit').read_text().strip()=='0')
    except (OSError,ValueError,KeyError):return False

def replace(s,a,b,n=1):
    assert s.count(a)==n,(a,s.count(a),n)
    return s.replace(a,b)

def render():
    cat=P/'inputs/cat60-execution-mix.sh';s=cat.read_text();original=s
    old=str(R/'result/mixX-cat60-90min-20261009/safety-env.sh')
    s=replace(s,old,str(P/'safety-env.sh'),2)
    s=replace(s,'[[ "$label" == mixX && "$policy" =~ ^arm[0-5][0-9]$ ]] || exit 2',
              '[[ ( "$label" == mixX || "$label" == mixY ) && "$policy" == onlinev7 && "${PH_SECS:-}" == 1800 && "$rep" == 1 ]] || exit 2\n[[ "$label" != mixY || "${MIXY_SEQ:-}" == "F S V F V S F S V F V S F S V F V S F S" ]] || exit 2')
    s=replace(s,'case "$policy" in','case "$policy" in\n    onlinev7) module="$root/buildoutput/nvmev-online-v7.ko";;')
    s=replace(s,'    mixX)  scale=1;','    mixX|mixY)  scale=1;')
    s=replace(s,'expected_arm=$((10#${policy#arm}))','expected_arm=37   # v7 initial arm, verified before preparation')
    upstream=(P/'inputs/script/mix-gc-20261010.sh').read_text()
    block=upstream[upstream.index('    mixY)  #'):upstream.index('    scrWP) A_NAME=')]
    s=replace(s,'    mixX)  #',block+'    mixX)  #')
    s=replace(s,'[[ $label != mixX ]] || for i in $(seq 1 3);','[[ $label != mixX && $label != mixY ]] || for i in $(seq 1 20);')
    s=replace(s,'[[ $label == mixX ]] || for sl in','[[ $label == mixX || $label == mixY ]] || for sl in')
    # Replace misleading generic two-phase journal description only for mixY.
    needle='elif [[ "$label" == mixX ]]; then'
    addition='elif [[ "$label" == mixY ]]; then\n'+'printf \'\\n### v7 mixY onlinev7 — started %s\\n- Sequence: %s; PH_SECS=%s; Table-3 prep; evidence `%s`; module `%s`.\\n\' "$(date -Is)" "$MIXY_SEQ" "$PH_SECS" "$dir" "$module" >> "$journal"\n'
    s=replace(s,needle,addition+needle)
    guard=(P/'inputs/cat60-safety-env.sh').read_text()
    guard=replace(guard,str(R/'result/mixX-cat60-90min-20261009/env-snapshot.sh'),str(P/'inputs/cat60-env-snapshot.sh'))
    guard=replace(guard,'[[ "$1" =~ ^/home/oy/iCAT/buildoutput/nvmev-arm[0-5][0-9]\\.ko$ ]] || return 1','[[ "$1" == /home/oy/iCAT/buildoutput/nvmev-online-v7.ko ]] || return 1')
    h=json.loads((P/'metadata.json').read_text())['module_sha256']
    guard=replace(guard,'   ;;\n  mkfs.ext4|mount|nvme)',f'   [[ "$(sha256sum "$1" | cut -d\' \' -f1)" == {h} ]] || return 1\n   ;;\n  mkfs.ext4|mount|nvme)')
    for name,body in [('execution-v7.sh',s),('safety-env.sh',guard)]:
        subprocess.run(['bash','-n'],input=body,text=True,check=True)
    return s,guard,''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile=str(cat),tofile='execution-v7.sh'))

def prepare():
    assert gate(),'CAT60 completion/push gate is closed'
    assert os.environ.get('MIXX_LOCK_HELD')=='1','caller must hold the common device lock'
    assert not Path('/sys/module/nvmev').exists(),'module occupied'
    s,g,d=render()
    for name,text in [('execution-v7.sh',s),('safety-env.sh',g),('runner-adaptation.diff',d)]:
        with (P/name).open('x') as f:f.write(text)
    subprocess.run(['bash','-n',str(P/'execution-v7.sh')],check=True)
    return {n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['execution-v7.sh','safety-env.sh']}
if __name__=='__main__':
    import sys
    if sys.argv[1:] == ['--preview']:
        s,g,d=render();print(d)
    else:print(json.dumps(prepare()))
