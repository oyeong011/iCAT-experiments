"""Read-only raw inputs; regenerate continuation inventory and failure list."""
from pathlib import Path
import csv,json
Q=Path(__file__).resolve().parent;P=Q.parent
meta=json.loads((Q/'metadata.json').read_text())
def write_csv(name,rows):
    with (Q/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def refresh():
    failures=[dict(policy='arm03',attempt='original',status='failed_byte_accounting_preserved',
                   byte_difference=520192,source=str(P/'mixX-arm03-rep1'))]
    valid={};attempts={}
    for n in range(30):
        policy=f'arm{n:02d}';base=P if n<3 else Q;f=base/f'{policy}-result.json'
        if not f.exists():continue
        d=json.loads(f.read_text());attempts[policy]=d
        if d['status']=='validated_saved_evidence':valid[policy]=d
        else:failures.append(dict(policy=policy,attempt='retry1' if n==3 else 'first',status=d['status'],
                                  byte_difference=d.get('byte_difference',''),source=d['raw_path']))
    write_csv('failures.csv',failures)
    missing=60-len(valid);rows=[]
    for n in range(60):
        policy=f'arm{n:02d}';d=valid.get(policy);a=attempts.get(policy,{})
        rank=1+sum(x['waf']<d['waf'] for x in valid.values()) if d else ''
        rows.append(dict(policy=policy,status=d['status'] if d else a.get('status','assigned_other_host' if n>=30 else 'pending'),
                         waf=d['waf'] if d else '',measured_rank=rank,rank_min=rank,rank_max=rank+missing if d else '',
                         measured_pool_size=len(valid),target_pool_size=60,source=a.get('raw_path',str((P if n<3 else Q)/f'mixX-{policy}-rep1')),
                         hostname=meta['hostname'],machine_id=meta['machine_id']))
    write_csv('inventory.csv',rows);write_csv('rank-reference.csv',rows)
    (Q/'ranking.txt').write_text(f'Valid local observations {len(valid)}/60; local assignment arm00-29. Other-host results not pooled.\n'
                               'Only valid results enter ranks; failed/missing arms widen rank ranges; single observations are not statistical superiority.\n'+
                               '\n'.join(f'{p}: WAF {d["waf"]:.6f}' for p,d in sorted(valid.items(),key=lambda x:x[1]['waf']))+'\n')
    return len(valid),len(failures)
if __name__=='__main__':print(refresh())
