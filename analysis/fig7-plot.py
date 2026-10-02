#!/usr/bin/env python3
"""그림 7. 워크로드 전환에 따른 파라미터 선택과 활성 후보 수 (iCAT-v4, 파티션 0, 3배 길이 1회차)
원천: figs/data/fig7_v4_trace.csv (analysis/fig7-data.py), 고정 비교선 figs/data/fig14_30s.csv"""
import csv
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
INK, INK2, GRID, V4, FIX = '#1a1a1a', '#5a5955', '#ecebe7', '#2a78d6', '#2b2a28'
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 10, 'axes.facecolor': 'white', 'figure.facecolor': 'white', 'axes.edgecolor': '#9a9994',
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6, 'axes.axisbelow': True,
                     'xtick.color': INK2, 'ytick.color': INK2, 'svg.fonttype': 'path'})
T = list(csv.DictReader(open('/home/oy/iCAT/figs/data/fig7_v4_trace.csv', encoding='utf-8-sig')))
F = list(csv.DictReader(open('/home/oy/iCAT/figs/data/fig14_30s.csv', encoding='utf-8-sig')))
def one(wl, out, a, b):
    t = [x for x in T if x['워크로드'] == wl and x['파티션'] == '0' and x['구간 WAF']]
    x = [float(r['경과(분)']) for r in t]; sw = next(float(r['경과(분)']) for r in t if r['구간'].startswith('뒤'))
    fig, ax = plt.subplots(3, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [1.3, 1.3, 0.9]})
    for a_ in ax: a_.axvspan(sw, max(x) + 0.5, color='#f2f6fc', zorder=0); a_.axvline(sw, color=INK2, ls='--', lw=1)
    f = [(float(r['경과(분)']), float(r['30초 WAF'])) for r in F if r['워크로드'] == wl and r['정책'] == 'CAT-47 (최적)' and r['30초 WAF']]
    ax[0].plot([p for p, _ in f], [w for _, w in f], color=FIX, lw=1.4, label='CAT-47 (최적 고정값) 30초 WAF — 비교 기준')
    ax[0].plot(x, [float(r['구간 WAF']) for r in t], color=V4, lw=0.9, marker='o', ms=2.5, label='iCAT-v4 판단 구간별 WAF')
    ax[0].set_ylabel('WAF (낮을수록 좋음)'); ax[0].legend(loc='upper left', fontsize=9, frameon=True, facecolor='white', edgecolor='#e0dfdb')
    st = [r['정착(1=예)'] == '1' for r in t]
    ax[1].scatter([p for p, s in zip(x, st) if not s], [int(r['이번 구간에 쓴 조합']) for r, s in zip(t, st) if not s], s=12, color='#a3a29d', label='탐색 중 시험한 조합')
    ax[1].scatter([p for p, s in zip(x, st) if s], [int(r['이번 구간에 쓴 조합']) for r, s in zip(t, st) if s], s=14, color=V4, label='정착 상태에서 쓴 조합')
    ax[1].plot(x, [int(r['추정 최선 조합']) for r in t], color=INK, lw=1, drawstyle='steps-post', label='추정 최선 조합')
    ax[1].set_ylabel('조합 번호 (15~59)'); ax[1].set_ylim(12, 62); ax[1].legend(loc='upper right', fontsize=9, frameon=True, facecolor='white', edgecolor='#e0dfdb')
    ax[2].plot(x, [int(r['남은 후보 수']) for r in t], color=V4, lw=2, drawstyle='steps-post'); ax[2].set_ylabel('남은 후보 수'); ax[2].set_ylim(0, 48)
    ax[2].set_xlabel('측정 시작 후 시간 (분)')
    for a_ in ax: a_.text(sw / 2, 1.02, f'앞: {a}', transform=a_.get_xaxis_transform(), ha='center', fontsize=9.5, color=INK2) if a_ is ax[0] else None
    ax[0].text(sw + (max(x) - sw) / 2, 1.02, f'뒤: {b}', transform=ax[0].get_xaxis_transform(), ha='center', fontsize=9.5, color=INK2)
    fig.suptitle(f'그림 7. {wl} 전환에서 iCAT-v4의 선택 과정 (파티션 0)', x=0.01, ha='left', fontsize=14, weight='bold', color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    for e in ('png', 'svg', 'pdf'): fig.savefig(f'/home/oy/iCAT/figs/{out}.{e}', dpi=220, bbox_inches='tight')
one('OLTP → Varmail', 'fig7_selection_oltp_varmail', 'OLTP', 'Varmail')
one('FIO-Fast → Varmail', 'fig7_selection_fio_varmail', 'FIO-Fast', 'Varmail')
