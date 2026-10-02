#!/usr/bin/env python3
"""전환 워크로드별 표 (3배 길이): 행 = 정책, 열 = 구간 A·B(·C) WAF, 전체 WAF, CAT-47 대비 -> MIX_TABLES.md"""
import re, glob, statistics as st, collections
from pathlib import Path
M = Path('/home/oy/iCAT/result/mix-20260911')
MIX = {'O': 'OLTP → Varmail', 'F': 'FIO-Fast → Varmail', 'J': 'YCSB-A → YCSB-B', 'P': 'YCSB-A → OLTP',
       'K': 'FIO-Fast (hot 512 → 128 MB)', 'D': 'FIO-Fast → FIO-Slow', 'H': 'FIO-Slow → FIO-Fast → YCSB-A', 'L': 'FIO-Fast ↔ FIO-Slow (60 s × 5)',
       'C': 'FIO-Slow → FIO-Fast', 'Q': 'FIO-Fast → 유휴 5분 → FIO-Fast', 'A': 'FIO-Fast → YCSB-A', 'B': 'YCSB-A → FIO-Fast', 'G': 'FIO-Fast ∥ YCSB-A (동시)'}
def name(p):
    return {'onlinev4': 'iCAT-v4', 'fixed47': 'CAT-47 (최적)', 'fixed50': 'CAT-50 (견고)', 'fixed37': 'CAT-37 (기본)', 'greedy': 'Greedy'}.get(p, p.replace('arm', 'CAT-'))
out = ['# 전환 워크로드별 결과표 (3배 길이, 구간 지정 계측)\n', '행 = 정책, 열 = 각 구간의 WAF와 전체 WAF. 여러 번 잰 정책은 평균(n = 횟수). 낮을수록 우수. 구간 WAF끼리 평균해도 전체 WAF가 되지 않는다(구간마다 쓰기량이 다름).\n',
       '원천: `result/mix-20260911/<워크로드>-<정책>-rep<n>-x3/summary.txt`. 생성: `python3 analysis/mix-tables.py`\n']
for k, title in MIX.items():
    g = collections.defaultdict(list); phases = None
    for d in glob.glob(str(M / f'mix{k}-*-rep[0-9]-x3')):
        f = Path(d) / 'summary.txt'
        if not f.exists() or (Path(d) / 'SUSPECT.txt').exists(): continue
        t = f.read_text(); tot = re.search(r'^total .*WAF=([\d.]+)', t, re.M)
        ph = re.findall(r'^phase([A-C])\(([^)]*)\) .*WAF=([\d.]+)', t, re.M)
        if not tot: continue
        phases = phases or [(a, n) for a, n, _ in ph]
        g[Path(d).name.split('-')[1]].append((float(tot[1]), {a: float(w) for a, _, w in ph}))
    if not g: continue
    ref = st.mean(x for x, _ in g['fixed47']) if 'fixed47' in g else None
    cols = [f'구간 {a} ({n})' for a, n in phases]
    out += [f'\n## {title}\n', '| 정책 | n | ' + ' | '.join(cols) + ' | 전체 WAF | CAT-47 대비 | 순위 |', '|---|---:|' + '---:|' * len(cols) + '---:|---:|---:|']
    rows = sorted(((st.mean(x for x, _ in v), p, v) for p, v in g.items()))
    for i, (m, p, v) in enumerate(rows, 1):
        pa = [f'{st.mean(r[a] for _, r in v if a in r):.3f}' for a, _ in phases]
        rel = f'{(m / ref - 1) * 100:+.1f}%' if ref else '–'
        b = '**' if p == 'onlinev4' else ''
        out.append(f'| {b}{name(p)}{b} | {len(v)} | ' + ' | '.join(pa) + f' | {b}{m:.3f}{b} | {rel} | {i}/{len(rows)} |')
Path('/home/oy/iCAT/MIX_TABLES.md').write_text('\n'.join(out) + '\n')
