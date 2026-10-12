"""Offline tests only: no device/module/runner execution or experimental IO."""
import tempfile,json,shutil,hashlib
from pathlib import Path
from unittest.mock import patch
import prepare,analyze
P=Path(__file__).resolve().parent;M=json.loads((P/'metadata.json').read_text())
results=[]
assert not prepare.gate();assert not (P/'execution-v7.sh').exists();results.append('active CAT gate closed; runner has not been materialized')
s,g,d=prepare.render();assert 'onlinev7)' in s and 'for w in F V O;' in s
assert 'for w in $MIXY_SEQ;' in s and 'seq 1 20' in s
for n in ['phase_fio','phase_filebench','phase_varmail']:
    original=(P/'inputs/cat60-execution-mix.sh').read_text()
    start=original.index(n+'()');end=original.find('\n}',start)+2 if n!='phase_varmail' else original.find('\n',start)
    assert original[start:end] in s,n
results.append('both shell scripts bash -n passed in memory; CAT FIO/Filebench functions unchanged')
with tempfile.TemporaryDirectory() as td:
    q=Path(td);(q/'result.json').write_text(json.dumps(dict(status='completed_assignment',current_policy='arm29')))
    (q/'arm29-result.json').write_text('{}');(q/'publish-arm29.exit').write_text('0\n')
    assert not prepare.gate(q);(q/'publish-final.exit').write_text('1\n');assert not prepare.gate(q)
    (q/'publish-final.exit').write_text('0\n');assert prepare.gate(q)
    (q/'result.json').write_text(json.dumps(dict(status='halted',current_policy='arm29')));assert not prepare.gate(q)
results.append('no start until terminal assignment and both arm29/final pushes succeed')
with tempfile.TemporaryDirectory() as td:
    base=Path(td);raw=base/'raw';raw.mkdir();(base/'metadata.json').write_text(json.dumps(M))
    original=Path(M['cat_resume'])/'mixX-arm25-rep1'
    wanted=['started.txt','stopped.txt','final-control.txt','prepared.txt','exit-code.txt','device.txt','environment.txt','block-stat-before.txt','block-stat-after.txt','block-stat-stop-before.txt','preset.json','prepare.json','summary.txt','control-series.txt']
    wanted+=['filebench-S02.txt','filebench-S03.txt','phase-S01.json']
    for slot in ['S01','S02','S03']:
        wanted += [f'phase-{slot}-{a}.{b}' for a,b in [('start','txt'),('end','txt'),('start','time'),('end','time')]]+[f'fio-file-{slot}-start.stat']
    for n in wanted:shutil.copyfile(original/n,raw/n)
    (raw/'environment.txt').write_text(M['kernel']+'\n'+M['module_sha256']+'\n')
    lines=[];stamp=0
    for slot in ['S01','S02','S03']:
        stamp+=1;lines.append(f'[{stamp}.0] mix-mixX-onlinev7-123 phase={slot} START')
        for part in range(4):
            stamp+=1;lines.append(f'[{stamp}.0] WATGC_V2 sample ns=0 part={part} epoch=1 window=1 arm=37 gc_count=1024')
        stamp+=1;lines.append(f'[{stamp}.0] mix-mixX-onlinev7-123 phase={slot} END')
    (raw/'kernel.log').write_text('\n'.join(lines)+'\n')
    with patch.object(analyze,'P',base):
        d=analyze.analyze('test_valid',raw,['F','V','O'],0)
        assert not d['issues'],d['issues'];assert d['status']=='validated_saved_evidence'
        assert len(d['sample_counts'])==12 and all(x['sample_lines']==1 for x in d['sample_counts'])
        (raw/'block-stat-after.txt').write_text(str(int((raw/'block-stat-after.txt').read_text())+1))
        failed=analyze.analyze('test_mismatch',raw,['F','V','O'],1)
        assert failed['status']=='failed_preserved' and failed['waf']==d['waf'] and failed['host_bytes_minus_block_stat']==-512
results.append('real CAT25 counters/FIO/Filebench logs with synthetic online markers pass; injected byte mismatch remains failed with diagnostic WAF')
text='[1] mix-mixY-onlinev7-1 phase=S01 START\n[2] WATGC_V2 sample ns=0 part=1 epoch=1\n[2] WATGC_V2 sample ns=0 part=1 epoch=1\n[3] mix-mixY-onlinev7-1 phase=S01 END\n[4] WATGC_V2 sample ns=0 part=1 epoch=1\n'
c,st,en,err,dup=analyze.sample_counts(text);assert c[('S01',0,1)]==1 and c[(None,0,1)]==1 and dup==1 and not err
results.append('sample parser partitions/phase boundaries/duplicate snapshots/outside-phase accounting verified')
print(json.dumps(dict(status='PASS',tests=results,note='offline fixture tests; not a v7 smoke experiment'),ensure_ascii=False,indent=2))
