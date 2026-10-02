#!/usr/bin/env python3
"""그림 14. 응용 전환 워크로드 4개: 30초마다 잰 WAF (iCAT-v4 / CAT-47 / CAT-50 / CAT-37, 3배 길이 1회차)
원천: result/mix-20260911/mix{O,F,J,P}-<정책>-rep1-x3/control-series.txt, phase-B-start.time, summary.txt"""
import re, glob, statistics as st, datetime as dt
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
SURF, INK, INK2, GRID = '#ffffff', '#1a1a1a', '#5a5955', '#ecebe7'
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 10, 'axes.facecolor': SURF, 'figure.facecolor': SURF, 'axes.edgecolor': '#9a9994',
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6, 'axes.axisbelow': True,
                     'lines.solid_joinstyle': 'round', 'xtick.color': INK2, 'ytick.color': INK2, 'svg.fonttype': 'path'})
M = Path('/home/oy/iCAT/result/mix-20260911')
POL = [('fixed37', 'CAT-37 (기본)', '#e3a33b', 1.3), ('fixed50', 'CAT-50 (견고)', '#a3a29d', 1.3), ('fixed47', 'CAT-47 (최적)', '#2b2a28', 1.3), ('onlinev4', 'iCAT-v4 (제안)', '#2a78d6', 2.4)]
MIX = [('O', 'OLTP', 'Varmail'), ('F', 'FIO-Fast', 'Varmail'), ('J', 'YCSB-A', 'YCSB-B'), ('P', 'YCSB-A', 'OLTP')]
def series(d):
    s = [tuple(map(int, m.groups())) for l in open(d / 'control-series.txt') if (m := re.match(r'(\d+) .*active=1 .*host_pages=(\d+) gc_pages=(\d+)', l))]
    t0 = s[0][0]; b = (dt.datetime.fromisoformat((d / 'phase-B-start.time').read_text().strip()).timestamp() - t0) / 60
    med = sorted(h1 - h0 for (_, h0, _), (_, h1, _) in zip(s, s[1:]))[len(s) // 2]
    # 30 s intervals with <10% of the usual host writes (app restart gap at a switch) have no meaningful ratio -> dropped
    return [((t - t0) / 60, 1 + (g1 - g0) / (h1 - h0) if h1 - h0 > 0.1 * med else float('nan')) for (_, h0, g0), (t, h1, g1) in zip(s, s[1:])], b   # nan = gap in the line, not a bridge
def final(m, p):
    xs = [float(re.search(r'^total .*WAF=([\d.]+)', open(f).read(), re.M)[1]) for f in glob.glob(str(M / f'mix{m}-{p}-rep[0-9]-x3/summary.txt'))]
    return st.mean(xs)
fig, axs = plt.subplots(2, 2, figsize=(14, 9.5)); axs = axs.ravel()
for ax, (m, a, b) in zip(axs, MIX):
    fin = {p: final(m, p) for p, *_ in POL}; best = min(fin, key=fin.get); sw = []
    for p, lab, col, lw in POL:
        pts, s = series(M / f'mix{m}-{p}-rep1-x3'); sw.append(s)
        ax.plot([x for x, _ in pts], [y for _, y in pts], color=col, lw=lw, label=f'{lab}   최종 WAF {fin[p]:.3f}' + ('  ← 1등' if p == best else ''), zorder=3 if p == 'onlinev4' else 2)
    s = st.mean(sw); x1 = ax.get_xlim()[1]
    ax.axvspan(s, x1, color='#f2f6fc', zorder=0); ax.set_xlim(0, x1)
    ax.text(s / 2, 1.02, f'앞: {a}', transform=ax.get_xaxis_transform(), ha='center', fontsize=10.5, weight='bold', color=INK)
    ax.text((s + x1) / 2, 1.02, f'뒤: {b}', transform=ax.get_xaxis_transform(), ha='center', fontsize=10.5, weight='bold', color=INK)
    ax.set_title(f'{a} → {b}', loc='left', fontsize=12.5, weight='bold', color=INK, pad=24)
    lo, hi = ax.get_ylim(); ax.set_ylim(lo, hi + (hi - lo) * 0.45)
    ax.legend(loc='upper left', fontsize=9, frameon=True, facecolor='white', edgecolor='#e0dfdb', framealpha=0.95)
    ax.set_xlabel('실험 시작 후 시간 (분)', color=INK2); ax.set_ylabel('30초마다 잰 WAF\n(낮을수록 좋음)', color=INK2)
fig.suptitle('그림 14. 응용 워크로드가 바뀔 때 30초마다 잰 WAF', x=0.01, ha='left', fontsize=15, weight='bold', color=INK)
fig.text(0.01, 0.945, '선 = 30초 동안의 WAF (낮을수록 SSD 내부 쓰기가 적음)   ·   흰 배경 = 앞 워크로드, 파란 배경 = 뒤 워크로드   ·   범례 숫자 = 실험이 끝났을 때의 전체 WAF (v4는 반복 평균)',
         fontsize=9.5, color=INK2)
fig.tight_layout(rect=(0, 0, 1, 0.93))
for e in ('png', 'pdf', 'svg'): fig.savefig(f'/home/oy/iCAT/figs/fig14_four_app_mixes.{e}', dpi=220, bbox_inches='tight')
