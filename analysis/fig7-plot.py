#!/usr/bin/env python3
"""그림 7. 워크로드 전환에 따른 학습 상태와 활성 후보 수 (iCAT-v4, 파티션 0, 3배 길이 1회차)
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
STATE = [('전수 순회', '#d9d9de'), ('탐색', '#8e8e93'), ('정착', V4)]
def states(t):   # 0 = sweep (until the first elimination after coverage), 1 = searching, 2 = settled
    out, swept = [], False
    for i, r in enumerate(t):
        if i and int(r['남은 후보 수']) < int(t[i - 1]['남은 후보 수']): swept = True
        out.append(2 if r['정착(1=예)'] == '1' else (1 if swept else 0))
    return out
def one(wl, out, a, b):
    t = [x for x in T if x['워크로드'] == wl and x['파티션'] == '0' and x['구간 WAF']]
    x = [float(r['경과(분)']) for r in t]; X1 = max(x) + 0.3
    sw = next(float(r['경과(분)']) for r in t if r['구간'].startswith('뒤'))
    act = [int(r['남은 후보 수']) for r in t]; stt = states(t)
    fig, ax = plt.subplots(3, 1, figsize=(11, 7.2), sharex=True, gridspec_kw={'height_ratios': [1.2, 0.16, 0.85], 'hspace': 0.32})
    for a_ in (ax[0], ax[2]): a_.axvspan(sw, X1, color=BG, zorder=0, lw=0)
    for a_ in ax: a_.set_xlim(0, X1)
    ax[0].text(sw / 2, 0.88, f'앞 워크로드: {a}', transform=ax[0].get_xaxis_transform(), ha='center', fontsize=11, color=INK2, weight='bold')
    ax[0].text((sw + X1) / 2, 0.4, f'뒤 워크로드: {b}', transform=ax[0].get_xaxis_transform(), ha='center', fontsize=11, color=V4, weight='bold')
    # (가) WAF
    for pol, lab, col, lw, ls in [('CAT-37 (기본)', 'CAT-37 (기본값)', '#e3a33b', 1.8, '-'), ('CAT-50 (견고)', 'CAT-50 (견고 설정)', '#8e8e93', 1.8, '-'),
                                  ('CAT-47 (최적)', 'CAT-47 (최적, 참고: 사후 튜닝값)', FIX, 1.0, (0, (4, 2)))]:
        f = [(float(r['경과(분)']), float(r['30초 WAF'])) for r in F if r['워크로드'] == wl and r['정책'] == pol and r['30초 WAF']]
        ax[0].plot([p for p, _ in f], [w for _, w in f], color=col, lw=lw, ls=ls, label=lab)
    ax[0].plot(x, [float(r['구간 WAF']) for r in t], color=V4, lw=1.3, alpha=0.95, label='iCAT-v4 (제안)', zorder=5)
    ax[0].set_ylabel('구간 WAF\n(낮을수록 좋음)'); ax[0].legend(loc='center left', fontsize=9.5, frameon=False, bbox_to_anchor=(0.02, 0.55))
    ax[0].set_title('(가) 판단 구간별 WAF', loc='left', fontsize=11, color=INK, weight='bold')
    # (나) 학습 상태 띠
    ends = x[1:] + [X1]
    for x0, x1_, s_ in zip(x, ends, stt): ax[1].axvspan(x0, x1_, color=STATE[s_][1], lw=0)
    ax[1].set_yticks([]); ax[1].grid(False); ax[1].spines['bottom'].set_visible(False)
    ax[1].set_title('(나) 학습 상태', loc='left', fontsize=11, color=INK, weight='bold')
    from matplotlib.patches import Patch
    ax[1].legend(handles=[Patch(color=c, label=n) for n, c in STATE], loc='lower right', bbox_to_anchor=(1.0, 1.05), ncol=3, fontsize=9.5, frameon=False, handlelength=1.2)
    # (다) 후보 수
    ax[2].fill_between(x, act, step='post', color=V4, alpha=0.12, lw=0); ax[2].plot(x, act, color=V4, lw=2.2, drawstyle='steps-post')
    ax[2].set_ylabel('남은 후보 수'); ax[2].set_ylim(0, 50); ax[2].set_yticks([0, 15, 30, 45])
    ax[2].set_title('(다) 활성 후보 수', loc='left', fontsize=11, color=INK, weight='bold'); ax[2].set_xlabel('측정 시작 후 시간 (분)')
    if min(act) < 45:
        i_cov = next(i for i in range(1, len(act)) if act[i] < 45); j = act.index(min(act))
        note(ax[2], x[j], act[j], f'{x[j] - x[i_cov]:.1f}분 만에 45 → {min(act)}개', dx=-1.2, dy=22, ha='right')
        if act[-1] > min(act): note(ax[2], x[-1], act[-1], f'이웃 탐침으로 {act[-1]}개까지 회복', dx=-2.5, dy=18, ha='right')
    ax[0].text(sw, 0.02, f' 전환 {sw:.1f}분', transform=ax[0].get_xaxis_transform(), fontsize=10, color='#e5484d', weight='bold', va='bottom')
    for a_ in ax: a_.axvline(sw, color='#e5484d', lw=1.1, ls=(0, (3, 3)))
    fig.suptitle(f'그림 7. {wl} 전환에서 iCAT-v4의 학습 상태와 활성 후보 수 변화', x=0.06, ha='left', y=0.995, fontsize=13.5, weight='bold', color=INK)
    fig.text(0.06, 0.95, '파티션 0의 학습 기록, 3배 길이 1회차. 비교선(고정 CAT)은 각각 별도 실행이라 전환 시점이 최대 약 1분 다르다.', fontsize=9.5, color=INK2)
    for e in ('png', 'svg', 'pdf'): fig.savefig(f'/home/oy/iCAT/figs/{out}.{e}', dpi=220, bbox_inches='tight')
one('OLTP → Varmail', 'fig7_selection_oltp_varmail', 'OLTP', 'Varmail')
one('FIO-Fast → Varmail', 'fig7_selection_fio_varmail', 'FIO-Fast', 'Varmail')
