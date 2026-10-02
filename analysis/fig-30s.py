#!/usr/bin/env python3
"""그림: 30초 구간 WAF — 고정 CAT(47·50번)도 흔들린다 -> figs/fig12_30s_waf.(png|pdf). 원천: 각 실행의 control-series.txt(30초 누적 카운터)"""
import re, datetime as dt
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 9.5, 'axes.facecolor': SURF, 'figure.facecolor': SURF, 'axes.edgecolor': INK2,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID, 'axes.axisbelow': True, 'lines.solid_joinstyle': 'round', 'lines.solid_capstyle': 'round', 'grid.linewidth': 0.6, 'legend.frameon': False, 'svg.fonttype': 'path'})
M = '/home/oy/iCAT/result/mix-20260911/'
POL = [('fixed47', 'CAT-47 (최적)', '#3d3c39'), ('fixed50', 'CAT-50 (견고)', '#9a9994'), ('onlinev4', 'iCAT-v4', '#2a78d6')]
def series(d):
    s = [tuple(map(int, m.groups())) for l in open(M + d + '/control-series.txt') if (m := re.match(r'(\d+) .*active=1 .*host_pages=(\d+) gc_pages=(\d+)', l))]
    t0 = s[0][0]; out = []
    for (a, h0, g0), (b, h1, g1) in zip(s, s[1:]):
        if h1 - h0 > 20000: out.append(((b - t0) / 60, 1 + (g1 - g0) / (h1 - h0), 1 + g1 / h1))
    return t0, out
fig, axs = plt.subplots(2, 2, figsize=(12, 6.4), sharex='col', gridspec_kw={'height_ratios': [2, 1]})
for c, (mix, x, name) in enumerate([('mixD', 'x6', 'FIO-Fast → FIO-Slow (6배, 약 2시간)'), ('mixO', 'x3', 'OLTP → Varmail (3배, 약 30분)')]):
    for p, lab, col in POL:
        d = f'{mix}-{p}-rep1-{x}'; t0, s = series(d)
        axs[0, c].plot([a for a, _, _ in s], [w for _, w, _ in s], color=col, lw=1.1 if p != 'onlinev4' else 1.4, label=lab, alpha=0.95)
        axs[1, c].plot([a for a, _, _ in s], [k for _, _, k in s], color=col, lw=1.8, label=lab)
        b = (dt.datetime.fromisoformat(open(M + d + '/phase-B-start.time').read().strip()).timestamp() - t0) / 60
    for r in (0, 1): axs[r, c].axvline(b, color=INK2, ls='--', lw=1)
    axs[0, c].text(b, axs[0, c].get_ylim()[1], ' 워크로드 전환', fontsize=8, color=INK2, va='top')
    axs[0, c].set_title(name, loc='left', fontsize=10, color=INK)
    axs[1, c].set_xlabel('측정 시작 후 경과 시간 (분)')
axs[0, 0].set_ylabel('30초 구간 WAF\n(낮을수록 우수)'); axs[1, 0].set_ylabel('누적 WAF')
axs[0, 0].legend(frameon=False, fontsize=8.5, loc='upper left')
fig.suptitle('그림 12. 고정 CAT도 FIO 구간에서는 30초 구간 WAF가 크게 흔들리고(위 왼쪽), 응용 구간에서는 거의 일정하다(위 오른쪽)', x=0.01, ha='left', fontsize=10.5, color=INK)
fig.tight_layout()
for e in ('png', 'pdf', 'svg'): fig.savefig(f'/home/oy/iCAT/figs/fig12_30s_waf.{e}', dpi=220, bbox_inches='tight')
