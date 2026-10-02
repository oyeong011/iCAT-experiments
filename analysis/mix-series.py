#!/usr/bin/env python3
"""전환 워크로드별 30초 시계열 (3배 길이, 1회차): 행 = 30초 시점, 열 = 정책별 30초 구간 WAF·누적 WAF -> figs/series/<워크로드>.csv
원천: 각 실행의 control-series.txt(30초마다 누적 host_pages·gc_pages), 구간 경계는 phase-<X>-start.time."""
import re, csv, datetime as dt
from pathlib import Path
M = Path('/home/oy/iCAT/result/mix-20260911'); OUT = Path('/home/oy/iCAT/figs/series'); OUT.mkdir(parents=True, exist_ok=True)
MIX = {'O': 'OLTP→Varmail', 'F': 'FIO-Fast→Varmail', 'J': 'YCSB-A→YCSB-B', 'P': 'YCSB-A→OLTP', 'K': 'FIO-Fast(hot512→128MB)',
       'D': 'FIO-Fast→FIO-Slow', 'H': 'FIO-Slow→FIO-Fast→YCSB-A', 'L': 'FIO-Fast↔FIO-Slow(60s×5)', 'C': 'FIO-Slow→FIO-Fast',
       'Q': 'FIO-Fast→유휴5분→FIO-Fast', 'A': 'FIO-Fast→YCSB-A', 'B': 'YCSB-A→FIO-Fast', 'G': 'FIO-Fast∥YCSB-A(동시)'}
POL = [('onlinev4', 'iCAT-v4'), ('fixed47', 'CAT-47'), ('fixed50', 'CAT-50')]
def run(d):
    s = [tuple(map(int, m.groups())) for l in open(d / 'control-series.txt') if (m := re.match(r'(\d+) .*active=1 .*host_pages=(\d+) gc_pages=(\d+)', l))]
    bounds = sorted((dt.datetime.fromisoformat(f.read_text().strip()).timestamp(), f.name[6]) for f in d.glob('phase-*-start.time'))
    rows = []; med = sorted(h1 - h0 for (_, h0, _), (_, h1, _) in zip(s, s[1:]))[len(s) // 2]   # intervals with <10% of usual host writes: ratio left blank
    for (a, h0, g0), (b, h1, g1) in zip(s, s[1:]):
        ph = [p for t, p in bounds if t <= b][-1:] or ['A']
        rows.append((round((b - s[0][0]) / 60, 2), ph[0], 1 + (g1 - g0) / (h1 - h0) if h1 - h0 > 0.1 * med else None, 1 + g1 / h1 if h1 else None))
    return rows
for k, title in MIX.items():
    R = {lab: run(M / f'mix{k}-{p}-rep1-x3') for p, lab in POL if (M / f'mix{k}-{p}-rep1-x3' / 'control-series.txt').exists()}
    if not R: continue
    n = max(map(len, R.values())); f = lambda x: '' if x is None else f'{x:.4f}'
    with open(OUT / f'{title}.csv', 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh); w.writerow(['경과(분)', '구간'] + [f'{l} 30초 WAF' for l in R] + [f'{l} 누적 WAF' for l in R])
        base = max(R.values(), key=len)
        for i in range(n):
            w.writerow([base[i][0], base[i][1]] + [f(r[i][2]) if i < len(r) else '' for r in R.values()] + [f(r[i][3]) if i < len(r) else '' for r in R.values()])
    print(f'{title}.csv  {n}행  정책: {", ".join(R)}')
