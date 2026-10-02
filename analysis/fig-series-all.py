#!/usr/bin/env python3
"""전환 워크로드마다 30초 구간 WAF: iCAT-v4 vs CAT-47 vs CAT-50 (3배 길이, 1회차) -> figs/series/png/<워크로드>.png + figs/fig13_series_all.png
원천: figs/series/<워크로드>.csv (analysis/mix-series.py)"""
import csv
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 9, 'axes.facecolor': SURF, 'figure.facecolor': SURF, 'axes.edgecolor': INK2,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID, 'axes.axisbelow': True})
COL = {'iCAT-v4': ('#2a78d6', 1.6), 'CAT-47': ('#3d3c39', 1.1), 'CAT-50': ('#a8a7a2', 1.1)}
S = Path('/home/oy/iCAT/figs/series'); P = S / 'png'; P.mkdir(exist_ok=True)
def load(f):
    r = list(csv.DictReader(open(f, encoding='utf-8-sig')))
    return r, [l for l in COL if f'{l} 30초 WAF' in r[0]]
def draw(ax, f, small=False):
    r, labs = load(f); x = [float(a['경과(분)']) for a in r]
    for l in labs:
        y = [float(a[f'{l} 30초 WAF']) if a[f'{l} 30초 WAF'] else None for a in r]
        ax.plot(x, y, color=COL[l][0], lw=COL[l][1], label=f"{l}  (누적 {next(float(a[f'{l} 누적 WAF']) for a in reversed(r) if a[f'{l} 누적 WAF']):.3f})")
    prev = r[0]['구간']
    for a in r:
        if a['구간'] != prev: ax.axvline(float(a['경과(분)']), color=INK2, ls='--', lw=1); ax.text(float(a['경과(분)']), 1, f' 구간 {a["구간"]}', transform=ax.get_xaxis_transform(), fontsize=7.5, color=INK2, va='top'); prev = a['구간']
    ax.set_title(f.stem, loc='left', fontsize=9.5 if small else 11, color=INK)
    ax.legend(frameon=False, fontsize=7 if small else 8.5, loc='upper left')
files = sorted(S.glob('*.csv'))
for f in files:
    fig, ax = plt.subplots(figsize=(10, 4)); draw(ax, f)
    ax.set_xlabel('측정 시작 후 경과 시간 (분)'); ax.set_ylabel('30초 구간 WAF (낮을수록 우수)')
    fig.tight_layout(); fig.savefig(P / f'{f.stem}.png', dpi=140); plt.close(fig)
fig, axs = plt.subplots(5, 3, figsize=(16, 19)); axs = axs.ravel()
for ax, f in zip(axs, files): draw(ax, f, small=True)
for ax in axs[len(files):]: ax.axis('off')
fig.suptitle('그림 13. 전환 워크로드별 30초 구간 WAF — iCAT-v4(파랑) · CAT-47(검정) · CAT-50(회색), 3배 길이 1회차, 범례 괄호 = 최종 누적 WAF', x=0.01, ha='left', fontsize=12, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.985)); fig.savefig('/home/oy/iCAT/figs/fig13_series_all.png', dpi=110)
print(len(files), 'workloads')
