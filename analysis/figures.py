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
named = {47: 'CAT-Best (47)', 50: 'CAT-Robust (50)', 37: 'CAT-Default (37)'}
ax.bar(range(60), [T[a] - 1 for a in order], bottom=1, width=0.8, color=['#9ec5f4' if a // 15 else '#d8d7d2' for a in order])
for i, a in enumerate(order):
    if a in named:
        ax.bar(i, T[a] - 1, bottom=1, width=0.8, color='#3d3c39'); ax.annotate(named[a], (i, T[a]), xytext=(0, 4), textcoords='offset points', ha='center', fontsize=8, color=INK)
ax.axhline(2.186, color=INK2, ls='--', lw=1); ax.text(0, 2.186 + 0.01, 'Greedy 2.186', ha='left', va='bottom', fontsize=8, color=INK2)
ax.set_ylim(1.0, 2.35); ax.set_xlim(-1, 60); ax.set_xticks([]); ax.set_xlabel('CAT 파라미터 조합 60개 (WAF 오름차순; 연한 파랑 k≥4, 연한 회색 k=2, 진한 회색 비교 기준 조합)'); ax.set_ylabel('WAF (낮을수록 우수, 1.0 = GC 복사 없음)')
ax.set_title('그림 1. CAT 파라미터 조합에 따른 WAF: 최대 28% 차이, 최하위는 k=2 조합\nFIO-Fast · 원저자 계측 방식 · 조합당 1회(10분)', loc='left', fontsize=10.5, color=INK)
save(fig, 'fig1_sensitivity')

# Fig 2 — cumulative WAF over time, fast 3-region writes (explicit method)
fig, ax = plt.subplots(figsize=(8, 3.8))
for key, d, lab in [('v1', 't4-online-rep1-x18', 'iCAT (원 구현)'), ('v2', 't4-onlinev2-rep1-x18', 'iCAT-v2'),
                    ('v3', 't4-onlinev3-rep1-x18', 'iCAT-v3'), ('v4', 't4-onlinev4-rep1-x60', 'iCAT-v4 (제안)')]:
    x, y = curve(d); k = [i for i, t in enumerate(x) if t >= 0.25]
    ax.plot([x[i] for i in k], [y[i] for i in k], color=C[key]); ax.text(x[-1] + 0.1, y[-1] + {'v1': 0.008, 'v2': -0.008}.get(key, 0), lab, color=INK, fontsize=9, va='center')
for v, lab in [(1.772, 'CAT-Best (arm 47) 1.772'), (1.814, 'CAT-Robust (arm 50) 1.814')]:
    ax.axhline(v, color=INK2, ls=':', lw=1.2); ax.text(0.3, v + 0.004, lab, color=INK2, fontsize=8, va='bottom', ha='left')
ax.set_xlim(0, 11); ax.set_ylim(1.74, 2.12); ax.set_xlabel('실행 시간 (h)'); ax.set_ylabel('누적 WAF (낮을수록 우수)')
ax.set_title('그림 2. 실행 시간에 따른 누적 WAF: iCAT-v4는 10시간에 CAT-Robust 수준 도달\nFIO-Fast · 명시 계측 · 정책별 1회 실행 · 초기 15분 제외', loc='left', fontsize=10.5, color=INK)
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
cols = [('상위 조합 (최상위 대비 WAF 3% 이내)', '#3d3c39'), ('중위 조합', '#c9c8c3'), ('저성능 조합 (최상위 대비 15% 초과)', NEG)]
for i, (lab, d) in enumerate(rows[::-1]):
    left = 0
    for (cl, cc), v in zip(cols, time_use(d)):
        ax.barh(i, v, left=left, color=cc, height=0.6, edgecolor=SURF, linewidth=2)
        if v > 0.025: ax.text(left + v / 2, i, f'{v:.0%}', ha='center', va='center', fontsize=8 if v > 0.06 else 7, color='white' if cc != '#c9c8c3' else INK)
        left += v
ax.set_yticks(range(4)); ax.set_yticklabels(['iCAT-v4 (제안)', 'iCAT-v3', 'iCAT-v2', 'iCAT (원 구현)']); ax.set_xlim(0, 1); ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.grid(axis='y', visible=False); ax.legend([plt.Rectangle((0, 0), 1, 1, color=c) for _, c in cols], [l for l, _ in cols], ncol=3, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.18), fontsize=8)
ax.set_title('그림 3. 학습기별 적용 조합의 분포: 저성능 조합 비율 21%(iCAT) → 12%(v3) → 4%(v4)\nFIO-Fast · 초기 3시간 · 정책별 1회 실행 · 조합 등급은 그림 1 기준', loc='left', fontsize=11, color=INK)
save(fig, 'fig3_time_use')

# Fig 4 — v4 vs robust CAT on 13 mixes at x3 (diverging)
MIX = {'O': 'OLTP → Varmail', 'F': 'FIO-Fast → Varmail', 'J': 'YCSB-A → YCSB-B', 'P': 'YCSB-A → OLTP',
       'K': 'FIO-Fast (hot 512 → 128 MB)', 'D': 'FIO-Fast → FIO-Slow', 'H': 'FIO-Slow → FIO-Fast → YCSB-A', 'L': 'FIO-Fast ↔ FIO-Slow (60 s × 5)',
       'C': 'FIO-Slow → FIO-Fast', 'Q': 'FIO-Fast → 유휴 5분 → FIO-Fast', 'A': 'FIO-Fast → YCSB-A', 'B': 'YCSB-A → FIO-Fast', 'G': 'FIO-Fast ∥ YCSB-A (동시)'}
d4 = {}; NREP = {}
for k, n in MIX.items():
    v = [x for r in (1, 2, 3) if (x := tot(f'mix{k}-onlinev4-rep{r}-x3'))]; f50 = tot(f'mix{k}-fixed50-rep1-x3')
    if v and f50: d4[n] = (st.mean(v) / f50 - 1) * 100; NREP[n] = len(v)
items = sorted(d4.items(), key=lambda x: x[1])
fig, ax = plt.subplots(figsize=(8, 4.6))
for i, (n, v) in enumerate(items[::-1]):
    ax.barh(i, v, color=POS if v < 0 else NEG, height=0.62)
    ax.text(v + (0.25 if v >= 0 else -0.25), i, f'{v:+.1f}%  (n={NREP[n]})', va='center', ha='left' if v >= 0 else 'right', fontsize=8, color=INK)
ax.axvline(0, color=INK2, lw=1); ax.set_yticks(range(len(items))); ax.set_yticklabels([n for n, _ in items[::-1]], fontsize=9)
ax.set_xlim(-10, 17); ax.grid(axis='y', visible=False); ax.set_xlabel('CAT-Robust 대비 iCAT-v4의 WAF 변화율 (%; 음수 = iCAT-v4 우수)')
ax.set_title('그림 4. 전환 워크로드별 CAT-Robust 대비 iCAT-v4의 WAF 변화율: 13종 중 4종에서 우수\n3배 길이(30~90분) · 명시 계측 · n = iCAT-v4 반복 횟수, CAT-Robust 1회', loc='left', fontsize=11, color=INK)
save(fig, 'fig4_mixes_v4_vs_robust')

# Fig 5 — 3-phase mix (fast -> SQLite -> fast), per phase
pol = [('CAT-Best', ['mixR-fixed47-rep1-x3'], '#6b6a66'), ('CAT-Robust', ['mixR-fixed50-rep1-x3', 'mixR-fixed50-rep2-x3'], '#b3b2ac'),
       ('iCAT', ['mixR-online-rep1-x3'], C['v1']), ('iCAT-v3', ['mixR-onlinev3-rep1-x3'], C['v3']), ('iCAT-v4', ['mixR-onlinev4-rep1-x3', 'mixR-onlinev4-rep2-x3'], C['v4'])]
fig, ax = plt.subplots(figsize=(8, 3.6)); W = 0.15
for j, (lab, ds, col) in enumerate(pol):
    ph = [phases(d) for d in ds]; ys = [st.mean(p[k] for p in ph) for k in 'ABC']
    ax.bar([i + (j - 2) * (W + 0.02) for i in range(3)], ys, width=W, color=col, label=f'{lab} (전체 {st.mean(tot(d) for d in ds):.3f}' + (f', n={len(ds)})' if len(ds) > 1 else ')'))
ax.set_xticks(range(3)); ax.set_xticklabels(['FIO-Fast (1구간)', 'YCSB-A (2구간)', 'FIO-Fast (3구간)']); ax.set_ylim(1.0, 4.0); ax.set_ylabel('구간 WAF (낮을수록 우수)')
ax.grid(axis='x', visible=False); ax.legend(ncol=3, frameon=False, loc='upper left', fontsize=8)
ax.set_title('그림 5. 3구간 전환 워크로드의 구간별 WAF: 학습기는 YCSB-A 구간에서 우수, iCAT-v4는 3구간 복귀가 빠름\nFIO-Fast → YCSB-A → FIO-Fast · 구간별 호스트 쓰기량 동일 · 3배 길이(약 2.3시간)', loc='left', fontsize=11, color=INK)
save(fig, 'fig5_three_phase_mix')

# Fig 6 — v3 ablation (fast 3-region, 3 h)
ab = [('iCAT-v3', tot('t4-onlinev3-rep1-x18')), ('v3 − 탐색 중단 (수렴 후 탐색 복원)', tot('t4-onlinev3probe-rep1-x18')),
      ('iCAT (원 구현)', tot('t4-online-rep1-x18')), ('v3 − k=2 제외 (k=2 조합 복원)', tot('t4-onlinev3k2-rep1-x18'))]
fig, ax = plt.subplots(figsize=(8, 2.6))
for i, (lab, v) in enumerate(ab[::-1]):
    ax.barh(i, v - 1, left=1, color=C['v3'] if 'v3' in lab else C['v1'], height=0.6)
    ax.text(v + 0.003, i, f'{v:.3f}', va='center', fontsize=8, color=INK)
ax.axvline(1.772, color=INK2, ls=':', lw=1.2); 
ax.set_yticks(range(len(ab))); ax.set_yticklabels([l for l, _ in ab[::-1]]); ax.set_xlim(1.0, 2.0); ax.grid(axis='y', visible=False)
ax.set_xlabel('3시간 누적 WAF (낮을수록 우수; 점선 = CAT-Best 1.772)'); ax.set_title('그림 6. iCAT-v3 구성 요소 제거 실험: k=2 제외 +3.1%, 수렴 후 탐색 중단 +1.5% 기여\nFIO-Fast · 3시간 · 명시 계측 · 정책별 1회 실행(기여 크기의 순서는 잠정)', loc='left', fontsize=11, color=INK)
save(fig, 'fig6_ablation')

# ---------------- 2026-10-01: transition workloads at x3 — v4 vs measured fixed arms ----------------
ARMS16 = {'fixed47': 47, 'fixed50': 50, 'fixed37': 37, **{f'arm{a:02d}': a for a in (46, 31, 32, 17, 16, 15, 30, 34, 35, 45, 49, 53, 56)}}
NAME = {'A': 'FIO-Fast → YCSB-A', 'C': 'FIO-Slow → FIO-Fast', **MIX}
LOSS = {}
for k in NAME:
    v = [x for r in (1, 2, 3) if (x := tot(f'mix{k}-onlinev4-rep{r}-x3'))]
    f3 = {p: x for p in ARMS16 if (x := tot(f'mix{k}-{p}-rep1-x3'))}
    if v and len(f3) >= 2:
        best = min(f3.values()); LOSS[k] = {'v4': (st.mean(v) / best - 1) * 100, **{p: (x / best - 1) * 100 for p, x in f3.items()}}

# Fig 7 — per workload: loss vs the best measured fixed arm (dots)
ks = sorted(LOSS, key=lambda k: LOSS[k]['v4'])
fig, ax = plt.subplots(figsize=(8, 0.55 * len(ks) + 1.4))
for i, k in enumerate(ks[::-1]):
    for p_, x in LOSS[k].items():
        if p_ == 'v4': continue
        ax.scatter(x, i, s=34, color='#6b6a66' if p_ == 'fixed47' else '#c9c8c3', zorder=2, edgecolor=SURF, linewidth=1, alpha=1 if len(LOSS[k]) >= 4 else 0.4)
    ax.scatter(LOSS[k]['v4'], i, s=60, color=C['v4'], zorder=3, edgecolor=SURF, linewidth=1.5)
    ax.text(LOSS[k]['v4'], i + 0.28, f"{LOSS[k]['v4']:+.1f}%", ha='center', fontsize=7, color=INK)
ax.axvline(0, color=INK2, lw=1); ax.set_ylim(-0.6, len(ks) - 0.1)
ax.set_yticks(range(len(ks))); ax.set_yticklabels([f'{NAME[k]} ({len(LOSS[k]) - 1}개)' + (' *' if len(LOSS[k]) < 4 else '') for k in ks[::-1]], fontsize=9)
ax.grid(axis='y', visible=False); ax.set_xlabel('측정한 고정 조합 중 최상위 대비 WAF 증가율 (%; 0 = 최상위와 동일, * 고정 조합 2개만 측정)')
ax.legend(handles=[plt.Line2D([], [], marker='o', ls='', color=C['v4'], label='iCAT-v4'), plt.Line2D([], [], marker='o', ls='', color='#6b6a66', label='CAT-Best (arm 47)'),
                   plt.Line2D([], [], marker='o', ls='', color='#c9c8c3', label='기타 고정 조합')], frameon=False, fontsize=8, loc='upper right')
ax.set_title('그림 7. 전환 워크로드별 최상위 고정 조합 대비 WAF 증가율\n3배 길이 · 괄호 = 측정한 고정 조합 수 · iCAT-v4 1~3회, 고정 조합 1회', loc='left', fontsize=11, color=INK)
save(fig, 'fig7_mix_loss_by_workload')

# Fig 8 — robustness: mean and worst loss over the workloads where every listed policy was measured
common = [k for k in LOSS if all(p_ in LOSS[k] for p_ in ('v4', 'fixed47', 'fixed50'))]
pols = [p_ for p_ in ['v4', 'fixed47', 'fixed50', 'arm17', 'fixed37', 'arm46', 'arm31'] if all(p_ in LOSS[k] for k in common)]
lab = {'v4': 'iCAT-v4', 'fixed47': 'CAT-Best\n(arm 47)', 'fixed50': 'CAT-Robust\n(arm 50)', 'fixed37': 'CAT-Default\n(arm 37)', 'arm17': 'arm 17', 'arm46': 'arm 46', 'arm31': 'arm 31'}
mean_ = [st.mean(LOSS[k][p_] for k in common) for p_ in pols]; worst = [max(LOSS[k][p_] for k in common) for p_ in pols]
fig, ax = plt.subplots(figsize=(8, 3.4)); W = 0.36
for j, (vals, col, name) in enumerate([(mean_, '#52514e', '평균 WAF 증가율'), (worst, '#b3b2ac', '최대 WAF 증가율')]):
    xs = [i + (j - 0.5) * (W + 0.03) for i in range(len(pols))]
    ax.bar(xs, vals, width=W, color=col, label=name)
    for x_, v_ in zip(xs, vals): ax.text(x_, v_ + 0.4, f'{v_:.1f}', ha='center', fontsize=7, color=INK)
ax.set_xticks(range(len(pols))); ax.set_xticklabels([lab[p_] for p_ in pols], fontsize=9); ax.grid(axis='x', visible=False)
ax.set_ylabel('최상위 고정 조합 대비 WAF 증가율 (%, 낮을수록 우수)'); ax.legend(frameon=False, fontsize=8, loc='upper left')
ax.set_title(f'그림 8. 전환 워크로드에서의 견고성: 평균은 CAT-Best, 최댓값은 iCAT-v4가 최소\n전환 워크로드 {len(common)}종 · 3배 길이 · 최상위는 측정한 고정 조합(2~6개) 기준', loc='left', fontsize=10.5, color=INK)
save(fig, 'fig8_robustness')

# ---------------- 2026-10-01: learning shown as rank among the 60 fixed arms ----------------
# Fig 9 — cumulative WAF over time expressed as a rank among fixed arms measured with the SAME (explicit) method.
EXPL = {a: tot(f't4-arm{a:02d}-rep1') for a in (31, 46, 32, 34, 16, 45, 49, 30, 35, 17, 15, 33)}
EXPL.update({47: tot('t4-fixed47-rep1'), 50: tot('t4long-fixed50-rep1'), 37: tot('t4-fixed37-rep1')})
EXPL = {a: v for a, v in EXPL.items() if v}
def rank_expl(v):  # arms not re-measured were all below 1.846 (original method) ~ 1.87+ explicit: rank capped at len+1
    return 1 + sum(x < v for x in EXPL.values())
fig, ax = plt.subplots(figsize=(8, 3.8))
for key, d, lab in [('v1', 't4-online-rep1-x18', 'iCAT'), ('v3', 't4-onlinev3-rep1-x18', 'iCAT-v3'), ('v4', 't4-onlinev4-rep1-x60', 'iCAT-v4')]:
    x, y = curve(d); k = [i for i, t in enumerate(x) if t >= 0.25]
    r = [rank_expl(y[i]) for i in k]
    ax.step([x[i] for i in k], r, where='post', color=C[key]); ax.text(x[-1] + 0.1, r[-1] + (0.6 if key == 'v4' else 0), f'{lab} {r[-1]}위' + (' (CAT-Robust 상회)' if key == 'v4' else ''), color=INK, fontsize=9, va='center')
for v, lab, xt in [(EXPL[47], 'CAT-Best (arm 47)', 5.0), (EXPL[50], 'CAT-Robust (arm 50)', 3.2), (EXPL[37], 'CAT-Default (arm 37; 전체 60개 중 약 21위)', 10.9)]:
    ax.axhline(rank_expl(v), color=INK2, ls=':', lw=1); ax.text(xt, rank_expl(v) - 0.25, lab, color=INK2, fontsize=8, ha='right' if xt > 10 else 'center', va='bottom')
ax.invert_yaxis(); ax.set_ylim(len(EXPL) + 1.5, 0); ax.set_xlim(0, 12.2)
ax.set_yticks([1, 5, 10, 15]); ax.set_ylabel('누적 WAF 기준 순위 (1 = 최상위)'); ax.set_xlabel('실행 시간 (h)')
ax.set_title(f'그림 9. 누적 WAF의 고정 조합 대비 순위 변화: iCAT-v4는 약 8시간 후 5위(CAT-Robust 상회)\nFIO-Fast · 정책별 1회 실행 · 명시 계측으로 재측정한 상위 고정 조합 {len(EXPL)}개 기준', loc='left', fontsize=10.5, color=INK)
save(fig, 'fig9_rank_over_time')

# Fig 10 — what v4 actually used: rank (among 60, original-method sweep) of the arm applied in each window, first 3 h
RANK60 = {a: i + 1 for i, a in enumerate(sorted(T, key=T.get))}
pts = []; t0 = None
for l in (M / 't4-onlinev4-rep1-x60' / 'kernel.log').read_text(errors='replace').splitlines():
    m = re.search(r'^\[\s*([\d.]+)\].*phase=measure evaluated=(\d+)', l)
    if not m: continue
    ts = float(m[1]); t0 = t0 or ts
    if ts - t0 > 3 * 3600: break
    pts.append(((ts - t0) / 3600, RANK60[int(m[2])]))
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.scatter([p_[0] for p_ in pts], [p_[1] for p_ in pts], s=5, color=C['v4'], alpha=0.35, linewidths=0)
B = 0.1; bins = {}
for t_, r_ in pts: bins.setdefault(int(t_ / B), []).append(r_)
bx = sorted(bins); ax.plot([(b + 0.5) * B for b in bx], [st.median(bins[b]) for b in bx], color=INK, lw=1.5)
ax.text(3.02, st.median(bins[bx[-1]]), '6분 구간 중앙값', fontsize=8, color=INK, va='center')
ax.invert_yaxis(); ax.set_ylim(61, 0); ax.set_yticks([1, 10, 20, 30, 40, 50, 60]); ax.set_xlim(0, 3.4)
ax.set_ylabel('적용 조합의 순위\n(60개 중, 1 = 최상위)'); ax.set_xlabel('실행 시간 (h)')
ax.set_title('그림 10. iCAT-v4가 판단 구간마다 적용한 조합의 순위: 약 1.5시간 후 상위 3위 부근으로 수렴\nFIO-Fast · 1회 실행 · 점 = 판단 구간 · 순위는 그림 1 기준', loc='left', fontsize=10.5, color=INK)
save(fig, 'fig10_v4_choices')
