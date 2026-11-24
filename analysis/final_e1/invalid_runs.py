#!/usr/bin/env python3
"""Run-level validity table for every run that has a YCSB (sqlite) phase. Uses validity.py.
Output: result/final-e1-validation/run_validity_ycsb.csv, phaseA_valid_runs.csv (derived files)."""
import csv, re, sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validity as V
ROOT = V.ROOT; OUT = ROOT / 'result/final-e1-validation'
rows = []
for s in sorted(ROOT.glob('result/**/summary.txt')):
    d = s.parent
    ph = V.phase_list(d)
    if not any('sqlite' in k or 'ycsb' in k for _, k in ph): continue
    use = V.usable_phases(d)
    seq = ' '.join(f'{p}:{k}' for p, k in ph)
    m = re.match(r'(mix[A-Z]\d?|t4\w*|[a-z]+)-(\w+?)-rep(\d+)(.*)$', d.name)
    rows.append(dict(group=str(d.parent.relative_to(ROOT)), run=d.name, workload=m[1] if m else '', policy=m[2] if m else '', rep=m[3] if m else '',
                     variant=m[4] if m else '', phases=seq, usable=''.join(sorted(use)) or '-', run_ok=V.run_ok(d),
                     first_valid_phase_A=('A' in use), reasons=' | '.join(V.reasons(d))))
with open(OUT / 'run_validity_ycsb.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
c = collections.Counter((r['group'], r['workload'] + r['variant'], 'OK' if r['run_ok'] else 'INVALID') for r in rows)
agg = collections.defaultdict(lambda: [0, 0])
for (g, wl, st), n in c.items(): agg[(g, wl)][0 if st == 'OK' else 1] += n
print(f'{"group":45s} {"workload":18s} ok invalid')
for (g, wl), (a, b) in sorted(agg.items()): print(f'{g:45s} {wl:18s} {a:3d} {b:3d}')
print('total runs', len(rows), 'ok', sum(r['run_ok'] for r in rows), 'invalid', sum(not r['run_ok'] for r in rows))

# ---- valid leading phases of runs that are not fully valid (e.g. mixR phase A) -> phase_prefix_valid.csv
pre = []
for r in rows:
    if r['run_ok'] or r['usable'] == '-': continue
    d = ROOT / r['group'] / r['run']; s = (d / 'summary.txt').read_text()
    for p, kind, h, g, w in re.findall(r'^phase([A-Z])\(([^)]*)\) host_pages=(\d+) gc_pages=(\d+) WAF=([\d.]+)', s, re.M):
        if p in r['usable']:
            pre.append(dict(group=r['group'], run=r['run'], workload=r['workload'], policy=r['policy'], rep=r['rep'], variant=r['variant'],
                            phase=p, kind=kind, host_pages=h, gc_pages=g, waf=w))
with open(OUT / 'phase_prefix_valid.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(pre[0])); w.writeheader(); w.writerows(pre)
print('valid leading phases from otherwise-invalid runs:', len(pre), collections.Counter((x['workload'], x['phase']) for x in pre))
# list in the "<path> <phases>" format validity.py reads (for cross-checking SeungCom's INVALID-20261124.txt)
with open(OUT / 'gocom_detected_invalid.txt', 'w') as f:
    f.write('# GoCom-detected invalid phases (YCSB failed ops > 1 %, and every later phase). Format: <run dir> <phases>\n')
    for r in rows:
        if not r['run_ok']:
            allp = [p for p, _ in V.phase_list(ROOT / r['group'] / r['run'])]
            bad = [p for p in allp if p not in r['usable']]
            f.write(f"{r['group']}/{r['run']} {','.join(bad)}  # {r['reasons'][:120]}\n")
