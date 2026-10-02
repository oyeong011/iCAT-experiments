#!/usr/bin/env python3
"""그림 7. 워크로드 전환에 따른 파라미터 선택과 활성 후보 수 (iCAT-v4, 파티션 0, 3배 길이 1회차)
원천: figs/data/fig7_v4_trace.csv (analysis/fig7-data.py), 고정 비교선 figs/data/fig14_30s.csv"""
import csv
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
INK, INK2, V4, FIX, PALE, BG = '#1d1d1f', '#6e6e73', '#2a78d6', '#1d1d1f', '#c7c7cc', '#f3f7fd'
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 10.5, 'axes.facecolor': 'white', 'figure.facecolor': 'white',
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False, 'axes.edgecolor': '#d2d2d7',
                     'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': '#ededf0', 'grid.linewidth': 0.8, 'axes.axisbelow': True,
                     'xtick.color': INK2, 'ytick.color': INK2, 'ytick.left': False, 'axes.labelcolor': INK2, 'svg.fonttype': 'path'})
T = list(csv.DictReader(open('/home/oy/iCAT/figs/data/fig7_v4_trace.csv', encoding='utf-8-sig')))
F = list(csv.DictReader(open('/home/oy/iCAT/figs/data/fig14_30s.csv', encoding='utf-8-sig')))
def note(ax, x, y, s, dx=0, dy=0, ha='left'):
    ax.annotate(s, (x, y), (x + dx, y + dy), fontsize=9.5, color=INK, ha=ha, va='center',
                arrowprops=dict(arrowstyle='-', color=INK2, lw=0.8, shrinkA=2, shrinkB=3), bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#d2d2d7', lw=0.8))
def one(wl, out, a, b):
    t = [x for x in T if x['워크로드'] == wl and x['파티션'] == '0' and x['구간 WAF']]
    x = [float(r['경과(분)']) for r in t]; X1 = max(x) + 0.3
    sw = next(float(r['경과(분)']) for r in t if r['구간'].startswith('뒤'))
    act = [int(r['남은 후보 수']) for r in t]; best = [int(r['추정 최선 조합']) for r in t]; arm = [int(r['이번 구간에 쓴 조합']) for r in t]
    fig, ax = plt.subplots(3, 1, figsize=(11, 8.6), sharex=True, gridspec_kw={'height_ratios': [1.1, 1.2, 0.8], 'hspace': 0.28})
    for a_ in ax: a_.axvspan(sw, X1, color=BG, zorder=0, lw=0); a_.set_xlim(0, X1)
    ax[0].text(sw / 2, 0.88, f'앞 워크로드: {a}', transform=ax[0].get_xaxis_transform(), ha='center', fontsize=11, color=INK2, weight='bold')
    ax[0].text((sw + X1) / 2, 0.6, f'뒤 워크로드: {b}', transform=ax[0].get_xaxis_transform(), ha='center', fontsize=11, color=V4, weight='bold')
    # (가) WAF
    f = [(float(r['경과(분)']), float(r['30초 WAF'])) for r in F if r['워크로드'] == wl and r['정책'] == 'CAT-47 (최적)' and r['30초 WAF']]
    ax[0].plot([p for p, _ in f], [w for _, w in f], color=FIX, lw=1.6, label='CAT-47 (최적 고정값)')
    ax[0].plot(x, [float(r['구간 WAF']) for r in t], color=V4, lw=1.1, alpha=0.9, label='iCAT-v4')
    ax[0].set_ylabel('구간 WAF\n(낮을수록 좋음)'); ax[0].legend(loc='center left', fontsize=9.5, frameon=False, bbox_to_anchor=(0.02, 0.55))
    ax[0].set_title('(가) 판단 구간별 WAF', loc='left', fontsize=11, color=INK, weight='bold')
    # (나) 조합
    ax[1].scatter(x, arm, s=7, color=PALE, zorder=2, label='그 구간에 시험·사용한 조합')
    ax[1].plot(x, best, color=V4, lw=2.2, drawstyle='steps-post', zorder=3, label='추정 최선 조합')
    ax[1].set_ylabel('조합 번호'); ax[1].set_ylim(10, 63); ax[1].set_yticks([15, 30, 45, 59])
    ax[1].legend(loc='upper right', fontsize=9.5, frameon=False, markerscale=2.5)
    ax[1].set_title('(나) 적용한 파라미터 조합', loc='left', fontsize=11, color=INK, weight='bold')
    i_cov = next(i for i in range(1, len(act)) if act[i] < 45) if min(act) < 45 else None
    k = min(range(len(x)), key=lambda i: abs(x[i] - sw * 0.45)); note(ax[1], x[k], arm[k], '전수 순회: 45개를 하나씩 측정', dx=-1.5, dy=20, ha='right')
    # (다) 후보 수
    ax[2].fill_between(x, act, step='post', color=V4, alpha=0.12, lw=0); ax[2].plot(x, act, color=V4, lw=2.2, drawstyle='steps-post')
    ax[2].set_ylabel('남은 후보 수'); ax[2].set_ylim(0, 50); ax[2].set_yticks([0, 15, 30, 45])
    ax[2].set_title('(다) 활성 후보 수', loc='left', fontsize=11, color=INK, weight='bold'); ax[2].set_xlabel('측정 시작 후 시간 (분)')
    if i_cov is not None:
        j = act.index(min(act)); note(ax[2], x[j], act[j], f'{x[j] - x[i_cov]:.1f}분 만에 45 → {min(act)}개', dx=-1.2, dy=22, ha='right')
        note(ax[2], x[-1], act[-1], f'이웃 탐침으로 {act[-1]}개까지 회복', dx=-2.5, dy=18, ha='right')
    for a_ in ax: a_.axvline(sw, color=INK2, lw=0.9, ls=(0, (3, 3)))
    fig.suptitle(f'그림 7. {wl} 전환에서 iCAT-v4의 파라미터 선택과 활성 후보 수 변화', x=0.06, ha='left', y=0.985, fontsize=13.5, weight='bold', color=INK)
    fig.text(0.06, 0.945, '파티션 0의 학습 기록, 3배 길이 1회차. 비교선 CAT-47은 별도 실행이라 전환 시점이 약 1분 다르다.', fontsize=9.5, color=INK2)
    for e in ('png', 'svg', 'pdf'): fig.savefig(f'/home/oy/iCAT/figs/{out}.{e}', dpi=220, bbox_inches='tight')
one('OLTP → Varmail', 'fig7_selection_oltp_varmail', 'OLTP', 'Varmail')
one('FIO-Fast → Varmail', 'fig7_selection_fio_varmail', 'FIO-Fast', 'Varmail')
