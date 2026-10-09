"""Rank only validated runs from this preregistered campaign."""
from pathlib import Path
import csv,json
P=Path(__file__).resolve().parent
meta=json.loads((P/'metadata.json').read_text())
valid={}
for policy in meta['policy_order']:
    f=P/f'{policy}-result.json'
    if f.exists():
        d=json.loads(f.read_text())
        if d.get('status')=='validated_saved_evidence':valid[policy]=d
missing=60-len(valid)
rows=[];phases=[]
for policy in meta['policy_order']:
    d=valid.get(policy);mod=meta['modules'][policy]
    rank=1+sum(v['waf']<d['waf'] for v in valid.values()) if d else ''
    row=dict(policy=policy,k=mod['k'],scale_pct=mod['scale_pct'],age_ratio=mod['age_ratio'],
             status='validated' if d else 'unmeasured_or_invalid',waf=d['waf'] if d else '',
             measured_rank=rank,rank_min=rank,rank_max=rank+missing if d else '',
             measured_pool_size=len(valid),target_pool_size=60,unmeasured_or_invalid=missing,
             hostname=meta['hostname'],machine_id=meta['machine_id'],seed='rep1',
             phase_seconds=meta['phase_seconds'],measurement='manual FTLpageWAF',
             actual_seconds=d['actual_measured_seconds'] if d else '',
             source=str(P/f'mixX-{policy}-rep1'),source_commit=meta['source_commit'])
    rows.append(row)
    for i,(slot,name) in enumerate(zip(meta['phase_slots'],meta['phase_order'])):
        phase=d['phases'][i] if d else None
        pr=1+sum(v['phases'][i]['waf']<phase['waf'] for v in valid.values()) if phase else ''
        phases.append(dict(policy=policy,slot=slot,workload=name,waf=phase['waf'] if phase else '',
                           rank_min=pr,rank_max=pr+missing if phase else '',measured_pool_size=len(valid),
                           target_pool_size=60,status=row['status'],source=row['source']))
for name,data in [('rank-reference.csv',rows),('phase-ranks.csv',phases),('inventory.csv',rows)]:
    with (P/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
ordered=sorted(valid.items(),key=lambda x:x[1]['waf'])
text=['# 90-minute FIO → Varmail → OLTP CAT ranking','',
      f'Validated {len(valid)}/60; unmeasured or invalid {missing}. Same host, one run per arm.',
      'Rank = 1 + count(validated fixed CAT WAF < target WAF). Missing arms widen the rank range.',
      'This is the 90-minute workload ranking, not the previous 10-hour mixX ranking.',
      'Small observed differences are not evidence of statistical superiority. 30-second samples are not independent repeats.',
      '', '| Measured rank | Arm | WAF | Possible rank among 60 |','|---:|---|---:|---|']
for policy,d in ordered:
    rank=1+sum(v['waf']<d['waf'] for v in valid.values())
    text.append(f'| {rank} | {policy} | {d["waf"]:.6f} | {rank}–{rank+missing} |')
(P/'ranking.md').write_text('\n'.join(text)+'\n')
print(json.dumps({'validated':len(valid),'missing_or_invalid':missing}))
