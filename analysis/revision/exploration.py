#!/usr/bin/env python3
"""Exploration counts per learner run from kernel.log WATGC lines (existing runs only).
Counts are summed over the 4 partitions. CPU columns come from the instrumented resource-v124 runs only."""
import csv, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT/'report/revision-20261123'; OUT.mkdir(parents=True, exist_ok=True)
RB = 'resource-overhead-20261114:result/resource-v124-20261114'
RUNS = [(f'iCAT {v}', 'FIO-Fast 30 min (resource-v124, instrumented)', f'git:{RB}/mixY-res{v}-rep{r}/kernel.log') for v in ('v1', 'v2', 'v4') for r in (1, 2, 3)] + [
    ('iCAT v1', 'mixR x3 Sep', 'result/mix-20260911/mixR-online-rep1-x3/kernel.log'),
    ('iCAT v3', 'mixR x3 Sep', 'result/mix-20260911/mixR-onlinev3-rep1-x3/kernel.log'),
    ('iCAT v4', 'mixR x3 Sep', 'result/mix-20260911/mixR-onlinev4-rep1-x3/kernel.log'),
    ('iCAT v4', 'mixR x3 Sep', 'result/mix-20260911/mixR-onlinev4-rep2-x3/kernel.log'),
    ('iCAT v4', 'mixY 10 h Nov', 'result/smartgc-20261119/resume/mixY-onlinev4-rep1/kernel.log'),
    ('iCAT v7', 'mixY 10 h Oct', 'result/v7-20261011/mixY/mixY-onlinev7-rep1/kernel.log')]
CAND = {'iCAT v1': 60, 'iCAT v2': 60, 'iCAT v3': 45, 'iCAT v4': 45, 'iCAT v7': 45}

def text(src):
    if src.startswith('git:'): return subprocess.run(['git', '-C', ROOT, 'show', src[4:]], capture_output=True, text=True).stdout
    return (ROOT/src).read_text(errors='replace')

rows = []
for pol, wl, src in RUNS:
    L = text(src).splitlines()
    per = {}
    for l in L:
        m = re.search(r'WATGC_V2 sample .*part=(\d) .*evaluated=(\d+)', l)
        if m:
            p = per.setdefault(m[1], {'arms': [], 'active': []}); p['arms'].append(int(m[2]))
            a = re.search(r'active=(\d+)', l)
            if a: p['active'].append(int(a[1]))
    win = sum(len(p['arms']) for p in per.values())
    rows.append({'policy': pol, 'workload': wl, 'candidates': CAND[pol], 'windows_evaluated': win,
        'arm_switches': sum(sum(a != b for a, b in zip(p['arms'], p['arms'][1:])) for p in per.values()),
        'distinct_arms_used': len({a for p in per.values() for a in p['arms']}),
        'drift_resets': sum(' reset ' in l and 'WATGC_V2' in l for l in L),
        'shift_resets_v6': sum('WATGC_V6 shift-reset' in l for l in L),
        'settled_events': sum('WATGC_V2 settled' in l for l in L),
        'min_active_per_part': min((min(p['active']) for p in per.values() if p['active']), default='미측정'),
        'final_active_sum': sum(p['active'][-1] for p in per.values() if p['active']) or '미측정',
        'source': src})
with open(OUT/'exploration_counts.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
if __name__ == '__main__':
    assert all(r['windows_evaluated'] > 0 for r in rows), [r['source'] for r in rows if not r['windows_evaluated']]
    for r in rows: print({k: v for k, v in r.items() if k != 'source'})
