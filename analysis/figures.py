#!/usr/bin/env python3
"""Paper figures from the raw result files -> figs/*.png, *.pdf.  python3 analysis/figures.py"""
import re, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
R = Path('/home/oy/iCAT/result'); M = R / 'mix-20260911'; OUT = Path('/home/oy/iCAT/figs'); OUT.mkdir(exist_ok=True)
# palette (validated: dataviz validate_palette.js, light surface): fixed entity -> colour in every figure
SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
C = {'v4': '#2a78d6', 'v1': '#eb6834', 'v3': '#1baf7a', 'v2': '#eda100'}
POS, NEG, MID = '#2a78d6', '#e34948', '#f0efec'          # diverging: learner better / worse
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 10, 'axes.edgecolor': INK2, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.facecolor': SURF, 'figure.facecolor': SURF,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID,
                     'grid.linewidth': 0.8, 'axes.axisbelow': True, 'lines.linewidth': 2})

def tot(d):
    f = M / d / 'summary.txt'
    m = re.search(r'^total .*WAF=([\d.]+)', f.read_text(), re.M) if f.exists() else None
    return float(m[1]) if m else None
def phases(d):
    f = M / d / 'summary.txt'
    return {k: float(w) for k, w in re.findall(r'^phase([ABC])\(\S*\) host_pages=\d+ gc_pages=\d+ WAF=([\d.]+)', f.read_text(), re.M)} if f.exists() else {}
def sweep(p): return {int(a): float(w) for a, w in re.findall(r'^\s*\d+\s+arm(\d\d)\s+\S+\s+([\d.]+)', Path(p).read_text(), re.M)}
def curve(d):  # cumulative WAF vs hours from the 30 s counter series
    rows = []
    for l in (M / d / 'control-series.txt').read_text().splitlines():
        s = l.split()
        if len(s) > 5 and s[4].startswith('host_pages='):
            h, g = int(s[4].split('=')[1]), int(s[5].split('=')[1])
            if h > 0: rows.append((int(s[0]), h, g))
    t0 = rows[0][0]
    return [(r[0] - t0) / 3600 for r in rows], [1 + r[2] / r[1] for r in rows]
def save(fig, name):
    fig.savefig(OUT / f'{name}.png', dpi=200, bbox_inches='tight'); fig.savefig(OUT / f'{name}.pdf', bbox_inches='tight'); plt.close(fig)
    print('wrote', name)

# Fig 1 — parameter sensitivity: 60 fixed arms on fast 3-region writes (original-author method)
T = sweep(R / 'sweep-20260915/rank-test4.txt'); order = sorted(T, key=T.get)
fig, ax = plt.subplots(figsize=(8, 3.2))
named = {47: '최적 (47)', 50: '견고 (50)', 37: '기본 (37)'}
ax.bar(range(60), [T[a] - 1 for a in order], bottom=1, width=0.8, color=['#9ec5f4' if a // 15 else '#d8d7d2' for a in order])
for i, a in enumerate(order):
    if a in named:
        ax.bar(i, T[a] - 1, bottom=1, width=0.8, color=C['v4']); ax.annotate(named[a], (i, T[a]), xytext=(0, 4), textcoords='offset points', ha='center', fontsize=8, color=INK)
ax.axhline(2.186, color=INK2, ls='--', lw=1); ax.text(0, 2.186 + 0.01, 'Greedy 2.186', ha='left', va='bottom', fontsize=8, color=INK2)
ax.set_ylim(1.0, 2.35); ax.set_xlim(-1, 60); ax.set_xticks([]); ax.set_xlabel('CAT 파라미터 조합 60개 (WAF 순서, 회색 = k=2)'); ax.set_ylabel('WAF (1.0 = GC 복사 없음)')
ax.set_title('그림 1. 빠른 3영역 쓰기에서 파라미터에 따른 WAF: 최대 28% 차이', loc='left', fontsize=11, color=INK)
save(fig, 'fig1_sensitivity')

# Fig 2 — cumulative WAF over time, fast 3-region writes (explicit method)
fig, ax = plt.subplots(figsize=(8, 3.8))
for key, d, lab in [('v1', 't4-online-rep1-x18', 'v1 (원래 iCAT)'), ('v2', 't4-onlinev2-rep1-x18', 'v2'),
                    ('v3', 't4-onlinev3-rep1-x18', 'v3'), ('v4', 't4-onlinev4-rep1-x60', 'v4')]:
    x, y = curve(d); k = [i for i, t in enumerate(x) if t >= 0.25]
    ax.plot([x[i] for i in k], [y[i] for i in k], color=C[key]); ax.text(x[-1] + 0.1, y[-1] + {'v1': 0.008, 'v2': -0.008}.get(key, 0), lab, color=INK, fontsize=9, va='center')
for v, lab in [(1.772, '최적 CAT 1.772'), (1.814, '견고 CAT 1.814')]:
    ax.axhline(v, color=INK2, ls=':', lw=1.2); ax.text(0.3, v + 0.004, lab, color=INK2, fontsize=8, va='bottom', ha='left')
ax.set_xlim(0, 11); ax.set_ylim(1.74, 2.12); ax.set_xlabel('실행 시간 (시간)'); ax.set_ylabel('누적 WAF')
ax.set_title('그림 2. 실행 시간에 따른 누적 WAF (빠른 3영역 쓰기, 첫 15분 제외)', loc='left', fontsize=11, color=INK)
save(fig, 'fig2_learning_over_time')

# Fig 3 — where each learner spends its windows (first 3 h, fast 3-region)
def time_use(d, hours=3):
    good = mid = bad = 0; best = min(T.values()); t0 = None
    for l in (M / d / 'kernel.log').read_text(errors='replace').splitlines():
        m = re.search(r'^\[\s*([\d.]+)\].*phase=measure evaluated=(\d+)', l)
        if not m: continue
        ts, a = float(m[1]), int(m[2]); t0 = t0 or ts
        if ts - t0 > hours * 3600: break
        w = T[a]; good += w <= best * 1.03; bad += w > best * 1.15; mid += best * 1.03 < w <= best * 1.15
    n = good + mid + bad; return [good / n, mid / n, bad / n]
fig, ax = plt.subplots(figsize=(8, 2.6))
rows = [('v1', 't4-online-rep1-x18'), ('v2', 't4-onlinev2-rep1-x18'), ('v3', 't4-onlinev3-rep1-x18'), ('v4', 't4-onlinev4-rep1-x60')]
cols = [('좋은 조합 (1등과 3% 이내)', C['v4']), ('중간', '#c9c8c3'), ('나쁜 조합 (15% 초과)', NEG)]
for i, (lab, d) in enumerate(rows[::-1]):
    left = 0
    for (cl, cc), v in zip(cols, time_use(d)):
        ax.barh(i, v, left=left, color=cc, height=0.6, edgecolor=SURF, linewidth=2)
        if v > 0.025: ax.text(left + v / 2, i, f'{v:.0%}', ha='center', va='center', fontsize=8 if v > 0.06 else 7, color='white' if cc != '#c9c8c3' else INK)
        left += v
ax.set_yticks(range(4)); ax.set_yticklabels(['v4', 'v3', 'v2', 'v1']); ax.set_xlim(0, 1); ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.grid(axis='y', visible=False); ax.legend([plt.Rectangle((0, 0), 1, 1, color=c) for _, c in cols], [l for l, _ in cols], ncol=3, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.18), fontsize=8)
ax.set_title('그림 3. 학습기가 처음 3시간 동안 쓴 조합 (빠른 3영역 쓰기; v4는 10시간 실행의 처음 3시간)', loc='left', fontsize=11, color=INK)
save(fig, 'fig3_time_use')

# Fig 4 — v4 vs robust CAT on 13 mixes at x3 (diverging)
MIX = {'O': '거래 DB 흉내 → 메일 서버', 'F': '빠른 3영역 → 메일 서버', 'J': 'SQLite 수정 많음 → 읽기 위주', 'P': 'SQLite → 거래 DB 흉내',
       'K': '뜨거운 구역 512 → 128 MB', 'D': '빠른 → 느린 3영역', 'H': '느린 → 빠른 → SQLite', 'L': '빠른 ↔ 느린 60초 × 5',
       'C': '느린 → 빠른 3영역', 'Q': '빠른 → 5분 쉼 → 빠른', 'A': '빠른 3영역 → SQLite', 'B': 'SQLite → 빠른 3영역', 'G': '빠른 3영역 + SQLite 동시'}
d4 = {}
for k, n in MIX.items():
    v = [x for r in (1, 2) if (x := tot(f'mix{k}-onlinev4-rep{r}-x3'))]; f50 = tot(f'mix{k}-fixed50-rep1-x3')
    if v and f50: d4[n] = (st.mean(v) / f50 - 1) * 100
items = sorted(d4.items(), key=lambda x: x[1])
fig, ax = plt.subplots(figsize=(8, 4.6))
for i, (n, v) in enumerate(items[::-1]):
    ax.barh(i, v, color=POS if v < 0 else NEG, height=0.62)
    ax.text(v + (0.25 if v >= 0 else -0.25), i, f'{v:+.1f}%', va='center', ha='left' if v >= 0 else 'right', fontsize=8, color=INK)
ax.axvline(0, color=INK2, lw=1); ax.set_yticks(range(len(items))); ax.set_yticklabels([n for n, _ in items[::-1]], fontsize=9)
ax.set_xlim(-8, 14); ax.grid(axis='y', visible=False); ax.set_xlabel('v4 WAF − 견고 CAT WAF (%)   ← v4가 좋음 | v4가 나쁨 →')
ax.set_title('그림 4. 전환 워크로드 13종에서 v4 대 견고 CAT (3배 길이)', loc='left', fontsize=11, color=INK)
save(fig, 'fig4_mixes_v4_vs_robust')

# Fig 5 — 3-phase mix (fast -> SQLite -> fast), per phase
pol = [('최적 47번', ['mixR-fixed47-rep1-x3'], '#6b6a66'), ('견고 50번', ['mixR-fixed50-rep1-x3', 'mixR-fixed50-rep2-x3'], '#b3b2ac'),
       ('v1', ['mixR-online-rep1-x3'], C['v1']), ('v3', ['mixR-onlinev3-rep1-x3'], C['v3']), ('v4', ['mixR-onlinev4-rep1-x3', 'mixR-onlinev4-rep2-x3'], C['v4'])]
fig, ax = plt.subplots(figsize=(8, 3.6)); W = 0.15
for j, (lab, ds, col) in enumerate(pol):
    ph = [phases(d) for d in ds]; ys = [st.mean(p[k] for p in ph) for k in 'ABC']
    ax.bar([i + (j - 2) * (W + 0.02) for i in range(3)], ys, width=W, color=col, label=lab)
ax.set_xticks(range(3)); ax.set_xticklabels(['빠른 3영역 (앞)', 'SQLite', '빠른 3영역 (뒤)']); ax.set_ylim(1.0, 3.6); ax.set_ylabel('구간 WAF (1.0 = GC 복사 없음)')
ax.grid(axis='x', visible=False); ax.legend(ncol=5, frameon=False, loc='upper left', fontsize=8)
ax.set_title('그림 5. 빠른 3영역 → SQLite → 빠른 3영역: 구간별 WAF (구간별 쓰기량 동일)', loc='left', fontsize=11, color=INK)
save(fig, 'fig5_three_phase_mix')

# Fig 6 — v3 ablation (fast 3-region, 3 h)
ab = [('v3', tot('t4-onlinev3-rep1-x18')), ('v3 + 정착 후 탐색 되돌림', tot('t4-onlinev3probe-rep1-x18')),
      ('v1 (원래 iCAT)', tot('t4-online-rep1-x18')), ('v3 + k=2 조합 되돌림', tot('t4-onlinev3k2-rep1-x18'))]
fig, ax = plt.subplots(figsize=(8, 2.6))
for i, (lab, v) in enumerate(ab[::-1]):
    ax.barh(i, v - 1, left=1, color=C['v3'] if lab.startswith('v3') else C['v1'], height=0.6)
    ax.text(v + 0.003, i, f'{v:.3f}', va='center', fontsize=8, color=INK)
ax.axvline(1.772, color=INK2, ls=':', lw=1.2); 
ax.set_yticks(range(len(ab))); ax.set_yticklabels([l for l, _ in ab[::-1]]); ax.set_xlim(1.0, 2.0); ax.grid(axis='y', visible=False)
ax.set_xlabel('WAF (3시간, 1.0 = GC 복사 없음)   점선 = 최적 CAT 1.772'); ax.set_title('그림 6. v3 변경을 하나씩 되돌렸을 때 (빠른 3영역 쓰기, 3시간)', loc='left', fontsize=11, color=INK)
save(fig, 'fig6_ablation')
