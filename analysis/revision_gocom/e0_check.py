#!/usr/bin/env python3
"""Independent recomputation of SeungCom E0 (Oct fixed47 module re-run in Nov, mixY S01-S04)
from raw phase counters, against the Oct fixed47 run and the Nov sg-arm47 runs.
Writes only result/revision-gocom-20261123/e0_*.csv (new files)."""
import csv, hashlib, os, re, sys
R = 'result'
RUNS = {
    'oct_fixed47_seungcom': f'{R}/gc-20261010/mixY-fixed47-rep1',
    'nov_E0_fixed47_seungcom': f'{R}/revision-20261123/check-fixed47-nov/mixY-fixed47-rep1',
    'nov_sg_arm47_seungcom': f'{R}/gc-20261010/mixY-sg-arm47-rep1',
    'nov_sg_arm47_gocom': f'{R}/gocom-sg-20261119/mixY-sg-arm47-rep1',
}
PH = ['S01', 'S02', 'S03', 'S04']
OUT = f'{R}/revision-gocom-20261123'

def counters(path):
    tot, parts = None, {}
    for line in open(path):
        m = re.match(r'epoch=\S+ active=\S+ host_bytes=\d+ host_pages=(\d+) gc_pages=(\d+)', line)
        if m: tot = tuple(map(int, m.groups()))
        m = re.match(r'part=(\d) host_pages=(\d+) gc_pages=(\d+)', line)
        if m: parts[int(m[1])] = (int(m[2]), int(m[3]))
    return tot, parts

def summary(path):
    d = {}
    for line in open(path):
        m = re.match(r'phase(S\d\d)\(\S+\) host_pages=(\d+) gc_pages=(\d+) WAF=([\d.]+)', line)
        if m: d[m[1]] = (int(m[2]), int(m[3]), float(m[4]))
    return d

def fb(path):
    if not os.path.exists(path): return ''
    m = re.search(r'IO Summary: \d+ ops ([\d.]+) ops/s', open(path).read())
    return m[1] if m else ''

def env(path, key):
    for line in open(path):
        if key in line: return line.strip()
    return ''

rows, errs = [], 0
for name, d in RUNS.items():
    summ = summary(f'{d}/summary.txt')
    for p in PH:
        (hs, gs), ps = counters(f'{d}/phase-{p}-start.txt')
        (he, ge), pe = counters(f'{d}/phase-{p}-end.txt')
        h, g = he - hs, ge - gs
        ph = sum(pe[i][0] - ps[i][0] for i in range(4)); pg = sum(pe[i][1] - ps[i][1] for i in range(4))
        waf = 1 + g / h
        sh, sg, sw = summ[p]
        ok = (h == sh and g == sg and h == ph and g == pg and abs(waf - sw) < 1e-6)
        errs += not ok
        t0 = open(f'{d}/phase-{p}-start.time').read().strip(); t1 = open(f'{d}/phase-{p}-end.time').read().strip()
        rows.append(dict(run=name, phase=p, host_pages=h, gc_pages=g, waf_recalc=f'{waf:.6f}',
                         waf_summary=f'{sw:.6f}', part_sum_match=h == ph and g == pg, summary_match=ok,
                         start=t0, end=t1, varmail_ops_s=fb(f'{d}/filebench-{p}.txt') if p == 'S03' else '',
                         per_part_waf=' '.join(f'{1+(pe[i][1]-ps[i][1])/(pe[i][0]-ps[i][0]):.4f}' for i in range(4))))
os.makedirs(OUT, exist_ok=True)
with open(f'{OUT}/e0_phase_recalc.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

envrows = []
for name, d in RUNS.items():
    e = f'{d}/environment.txt'
    ko = [l.split()[0][:16] + '  ' + os.path.basename(l.split()[1]) for l in open(e) if l.strip().endswith('.ko')]
    envrows.append(dict(run=name, date=open(e).readline().strip(), module=';'.join(ko),
                        cpu_scaling=env(e, 'scaling MHz').split(':')[-1].strip(),
                        model=env(e, 'Model name').split(':')[-1].strip(),
                        mem=env(e, 'Mem:'), fio_test4=env(e, 'mix-test4.fio').split()[0][:16] if env(e, 'mix-test4.fio') else ''))
with open(f'{OUT}/e0_environment.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(envrows[0])); w.writeheader(); w.writerows(envrows)

# closeness: S03/S04 distance to Oct vs Nov (pre-registered criterion)
W = {(r['run'], r['phase']): float(r['waf_recalc']) for r in rows}
for p in ['S03', 'S04']:
    e0 = W[('nov_E0_fixed47_seungcom', p)]; o = W[('oct_fixed47_seungcom', p)]; n = W[('nov_sg_arm47_seungcom', p)]
    print(f'{p}: E0={e0:.4f} Oct={o:.4f} (|d|={abs(e0-o):.4f}, {100*(e0-o)/o:+.2f}%) '
          f'Nov={n:.4f} (|d|={abs(e0-n):.4f}, {100*(e0-n)/n:+.2f}%)')
print('mismatches', errs)
for r in envrows: print(r)

# --- first Varmail phase after FIO, all arm-47 runs on SeungCom with the same varmail.f (raw counters) ---
FIRST_V = [
    ('2026-10-08', 'cycle-20261007/mixX-fixed47-rep1', 'S02', 'F V'),
    ('2026-10-10', 'gc-20261010/mixY-fixed47-rep1', 'S03', 'F S V'),
    ('2026-10-11', 'cat60-90min-thispc-20261011/mixY-arm47-rep1', 'S02', 'F V'),
    ('2026-10-13', 'cat60-90min-thispc-20261011/mixY-arm47-rep2', 'S02', 'F V'),
    ('2026-10-13', 'cat60-90min-thispc-20261011/mixY-arm47-rep3', 'S02', 'F V'),
    ('2026-11-20', 'gc-20261010/mixY-sg-arm47-rep1', 'S03', 'F S V'),
    ('2026-11-23', 'revision-20261123/check-fixed47-nov/mixY-fixed47-rep1', 'S03', 'F S V'),
]
fv = []
for date, d, p, seq in FIRST_V:
    d = f'{R}/{d}'
    (hs, gs), _ = counters(f'{d}/phase-{p}-start.txt'); (he, ge), _ = counters(f'{d}/phase-{p}-end.txt')
    ko = [l.split()[0][:16] for l in open(f'{d}/environment.txt') if l.strip().endswith('.ko')][0]
    vf = hashlib.sha256(open(f'{d}/varmail.f', 'rb').read()).hexdigest()[:12]
    fv.append(dict(date=date, run=d, phase=p, preceding=seq, module=ko, varmail_f=vf,
                   host_pages=he - hs, gc_pages=ge - gs, waf=f'{1 + (ge - gs) / (he - hs):.4f}',
                   varmail_ops_s=fb(f'{d}/filebench-{p}.txt')))
with open(f'{OUT}/e0_first_varmail_arm47.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(fv[0])); w.writeheader(); w.writerows(fv)
for r in fv: print(r['date'], r['preceding'], r['module'], r['waf'], r['varmail_ops_s'], r['run'])
