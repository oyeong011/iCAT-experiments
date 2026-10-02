#!/usr/bin/env python3
"""그림 14. 응용 전환 워크로드 4개: 30초 구간 WAF(왼쪽)와 누적 WAF(오른쪽), iCAT-v4 / CAT-47 / CAT-50 / CAT-37, 3배 길이 1회차
원천: result/mix-20260911/mix{O,F,J,P}-<정책>-rep1-x3/control-series.txt, phase-B-start.time, summary.txt"""
import re, glob, statistics as st, datetime as dt
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 9.5, 'axes.facecolor': SURF, 'figure.facecolor': SURF, 'axes.edgecolor': INK2,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID, 'axes.axisbelow': True})
M = Path('/home/oy/iCAT/result/mix-20260911')
POL = [('onlinev4', 'iCAT-v4', '#2a78d6', 1.8), ('fixed47', 'CAT-47 (최적)', '#2b2a28', 1.2), ('fixed50', 'CAT-50 (견고)', '#9a9994', 1.2), ('fixed37', 'CAT-37 (기본)', '#e0a33a', 1.2)]
MIX = [('O', 'OLTP → Varmail'), ('F', 'FIO-Fast → Varmail'), ('J', 'YCSB-A → YCSB-B'), ('P', 'YCSB-A → OLTP')]
def series(d):
    s = [tuple(map(int, m.groups())) for l in open(d / 'control-series.txt') if (m := re.match(r'(\d+) .*active=1 .*host_pages=(\d+) gc_pages=(\d+)', l))]
    t0 = s[0][0]; b = (dt.datetime.fromisoformat((d / 'phase-B-start.time').read_text().strip()).timestamp() - t0) / 60
    med = sorted(h1 - h0 for (_, h0, _), (_, h1, _) in zip(s, s[1:]))[len(s) // 2]
    # ponytail: 30 s intervals with <10% of the usual host writes (YCSB restart gap at a switch) give a meaningless ratio -> dropped
    pts = [((t - t0) / 60, 1 + (g1 - g0) / (h1 - h0), 1 + g1 / h1) for (_, h0, g0), (t, h1, g1) in zip(s, s[1:]) if h1 - h0 > 0.1 * med]
    return pts, b
def mean_total(m, p):
    xs = [float(re.search(r'^total .*WAF=([\d.]+)', open(f).read(), re.M)[1]) for f in glob.glob(str(M / f'mix{m}-{p}-rep[0-9]-x3/summary.txt'))]
    return st.mean(xs), len(xs)
fig, axs = plt.subplots(4, 2, figsize=(13, 15), gridspec_kw={'width_ratios': [1.6, 1]})
for r, (m, title) in enumerate(MIX):
    for p, lab, col, lw in POL:
        pts, b = series(M / f'mix{m}-{p}-rep1-x3'); mt, n = mean_total(m, p)
        x = [a for a, _, _ in pts]
        axs[r, 0].plot(x, [w for _, w, _ in pts], color=col, lw=lw, label=f'{lab}  최종 {mt:.3f}' + (f' ({n}회 평균)' if n > 1 else ''))
        axs[r, 1].plot(x, [c for _, _, c in pts], color=col, lw=lw + 0.4)
        for ax in axs[r]: ax.axvline(b, color=col, ls=':', lw=1.1)
    axs[r, 0].set_title(f'{title}   (점선 = 각 정책의 전환 시점)', loc='left', fontsize=10.5, color=INK)
    axs[r, 1].set_title('누적 WAF', loc='left', fontsize=10, color=INK2)
    axs[r, 0].set_ylabel('30초 구간 WAF\n(낮을수록 우수)'); axs[r, 0].legend(frameon=False, fontsize=8.5, loc='upper left')
for ax in axs[-1]: ax.set_xlabel('측정 시작 후 경과 시간 (분)')
fig.suptitle('그림 14. 응용 전환 워크로드 4개의 30초 구간 WAF와 누적 WAF (3배 길이 1회차, 범례 = 최종 전체 WAF)', x=0.01, ha='left', fontsize=12, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.98))
for e in ('png', 'pdf'): fig.savefig(f'/home/oy/iCAT/figs/fig14_four_app_mixes.{e}', dpi=130)
