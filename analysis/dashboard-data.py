#!/usr/bin/env python3
"""Data for the results dashboard (JSON on stdout), all from raw result files."""
import re, json, statistics as st
from pathlib import Path
M = Path('/home/oy/iCAT/result/mix-20260911')
def tot(d):
    f = M / d / 'summary.txt'
    if not f.exists() or (M / d / 'SUSPECT.txt').exists(): return None
    m = re.search(r'^total .*WAF=([\d.]+)', f.read_text(), re.M); return float(m[1]) if m else None
def series(d):
    rows = []
    for l in (M / d / 'control-series.txt').read_text().splitlines():
        s = l.split()
        if len(s) > 5 and s[4].startswith('host_pages='):
            h, g = int(s[4].split('=')[1]), int(s[5].split('=')[1])
            if h > 0: rows.append((int(s[0]), h, g))
    t0 = rows[0][0]; return [((r[0] - t0) / 3600, 1 + r[2] / r[1]) for r in rows]
EXPL = {a: tot(f't4-arm{a:02d}-rep1') for a in (31, 46, 32, 34, 16, 45, 49, 30, 35, 17, 15, 33)}
EXPL.update({47: tot('t4-fixed47-rep1'), 50: tot('t4long-fixed50-rep1'), 37: tot('t4-fixed37-rep1')})
EXPL = {a: v for a, v in EXPL.items() if v}
rank = lambda v: 1 + sum(x < v for x in EXPL.values())
curves = {}
for k, d in [('v1', 't4-online-rep1-x18'), ('v3', 't4-onlinev3-rep1-x18'), ('v4', 't4-onlinev4-rep1-x60')]:
    pts = [p for p in series(d) if p[0] >= 0.25]
    step = max(1, len(pts) // 160)
    curves[k] = [[round(t, 3), round(w, 4), rank(w)] for t, w in pts[::step]] + [[round(pts[-1][0], 3), round(pts[-1][1], 4), rank(pts[-1][1])]]
MIX = {'O': '거래 DB 흉내 → 메일 서버', 'F': '빠른 3영역 → 메일 서버', 'J': 'SQLite 수정 많음 → 읽기 위주', 'P': 'SQLite → 거래 DB 흉내',
       'K': '뜨거운 구역 512 → 128 MB', 'D': '빠른 → 느린 3영역', 'H': '느린 → 빠른 → SQLite', 'L': '빠른 ↔ 느린 60초 × 5',
       'C': '느린 → 빠른 3영역', 'Q': '빠른 → 5분 쉼 → 빠른', 'A': '빠른 3영역 → SQLite', 'B': 'SQLite → 빠른 3영역', 'G': '빠른 3영역 + SQLite 동시'}
ARMS = ['fixed47', 'fixed50', 'fixed37'] + [f'arm{a:02d}' for a in (46, 31, 32, 17, 16, 15, 30, 34, 35, 45, 49, 53, 56)]
mixes = []
for k, n in MIX.items():
    v = [x for r in (1, 2, 3) if (x := tot(f'mix{k}-onlinev4-rep{r}-x3'))]
    f3 = {a: x for a in ARMS if (x := tot(f'mix{k}-{a}-rep1-x3'))}
    if not v: continue
    best = min(f3, key=f3.get) if len(f3) >= 3 else None
    mixes.append({'name': n, 'v4': round(st.mean(v), 4), 'n': len(v), 'basic': f3.get('fixed37'), 'robust': f3.get('fixed50'), 'opt': f3.get('fixed47'),
                  'best': f3.get(best) if best else None, 'bestArm': int(re.sub(r'\D', '', best)) if best else None, 'fixedCount': len(f3)})
common = [m for m in mixes if m['robust'] and m['opt'] and m['fixedCount'] >= 2]
def loss(m, key):
    f = [x for x in (m['basic'], m['robust'], m['opt'], m['best']) if x]
    b = min(f); return (m[key] / b - 1) * 100
rob = {key: {'mean': round(st.mean(loss(m, key) for m in common), 2), 'worst': round(max(loss(m, key) for m in common), 2)} for key in ('v4', 'opt', 'robust')}
print(json.dumps({'curves': curves, 'ref': {'opt': EXPL[47], 'robust': EXPL[50], 'basic': EXPL[37], 'greedy': tot('t4long-greedy-rep1'), 'nFixed': len(EXPL)},
                  'ranks': {'opt': rank(EXPL[47]), 'robust': rank(EXPL[50]), 'basic': rank(EXPL[37])}, 'mixes': mixes, 'robust': rob, 'robustN': len(common)}, ensure_ascii=False))
