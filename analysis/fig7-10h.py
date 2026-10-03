#!/usr/bin/env python3
"""그림 7 (10시간판). OLTP -> Varmail 10시간: 30초 구간 WAF(iCAT-v4 vs 견고 CAT-50 vs 기본 CAT-37), v4 학습 상태, 활성 후보 수
-> figs/fig7_10h.(png|svg|pdf), figs/data/fig7_10h.xlsx (데이터 + 엑셀 차트, 직접 편집용)
원천: result/mix-20260911/mixO-<정책>-rep1-x20/control-series.txt (30초 누적 카운터), figs/data/fig7_v4_trace.csv (analysis/fig7-data.py).
CAT-37은 두 번째 PC 결과(FIXED37 경로)가 있을 때만 그린다. 없는 고정값은 건너뛴다."""
import csv, re, sys, datetime as dt
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch
from openpyxl import Workbook
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.styles import Font
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
M = Path('/home/oy/iCAT/result/mix-20260911')
FIXED37 = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/home/oy/iCAT/result/mixO-fixed37-chunked-20261003/mixO-fixed37-rep1-x20')   # second PC (icat-2), validated: CAT-47/50 within 0.2% of this PC
PART = '2'   # partition shown; the other three are drawn thin in panel (다)
INK, INK2, V4, RED, PUR = '#1d1d1f', '#6e6e73', '#2a78d6', '#e5484d', '#7d3cff'
POL = [('iCAT-v4 (제안)', M / 'mixO-onlinev4-rep1-x20', V4, 1.4), ('CAT-50 (견고 설정)', M / 'mixO-fixed50-rep1-x20', '#8e8e93', 1.6),
       ('CAT-37 (기본값)', FIXED37, '#e3a33b', 1.6)]
STATE = [('전수 순회', '#d9d9de'), ('탐색', '#8e8e93'), ('정착', V4)]
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 10.5, 'axes.facecolor': 'white', 'figure.facecolor': 'white',
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False, 'axes.edgecolor': '#d2d2d7',
                     'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': '#ededf0', 'grid.linewidth': 0.8, 'axes.axisbelow': True,
                     'xtick.color': INK2, 'ytick.color': INK2, 'ytick.left': False, 'axes.labelcolor': INK2, 'svg.fonttype': 'path'})

def series(d):   # 30 s WAF, hours since measurement start; near-empty intervals (<10% of usual writes) dropped
    s = [tuple(map(int, m.groups())) for l in open(d / 'control-series.txt') if (m := re.match(r'(\d+) .*active=1 .*host_pages=(\d+) gc_pages=(\d+)', l))]
    med = sorted(h1 - h0 for (_, h0, _), (_, h1, _) in zip(s, s[1:]))[len(s) // 2]
    return [((t - s[0][0]) / 3600, 1 + (g1 - g0) / (h1 - h0)) for (_, h0, g0), (t, h1, g1) in zip(s, s[1:]) if h1 - h0 > 0.1 * med], s[0][0]
def binned(d, t0, step_h, lo=0.0, hi=99.0):   # WAF of each bin = Δgc/Δhost over the bin (exact, from cumulative counters)
    raw = [tuple(map(int, m.groups())) for l in open(d / 'control-series.txt') if (m := re.match(r'(\d+) .*active=1 .*host_pages=(\d+) gc_pages=(\d+)', l))]
    s = [((t - t0) / 3600, h, g) for t, h, g in raw]
    out, k = [], lo
    while k + step_h <= min(hi, s[-1][0]) + 1e-9:
        a_ = min(s, key=lambda p: abs(p[0] - k)); b_ = min(s, key=lambda p: abs(p[0] - k - step_h))
        if b_[1] > a_[1]: out.append((k + step_h / 2, 1 + (b_[2] - a_[2]) / (b_[1] - a_[1])))
        k += step_h
    return out
def bin_steps(xs, ys, step_h, lo, hi, how):   # per bin: last value (candidates) or the state held longest (state)
    out, k = [], lo
    while k + step_h <= hi + 1e-9:
        idx = [i for i in range(len(xs)) if k <= xs[i] < k + step_h]
        if idx:
            v = ys[idx[-1]] if how == 'last' else max(set(ys[i] for i in idx), key=[ys[i] for i in idx].count)
            out.append((k + step_h / 2, v))
        k += step_h
    return out
def total(d):
    return float(re.search(r'^total .*WAF=([\d.]+)', (d / 'summary.txt').read_text(), re.M)[1])

pol = [(lab, d, c, lw) for lab, d, c, lw in POL if (d / 'summary.txt').exists()]
W = {lab: series(d) for lab, d, *_ in pol}
t0 = W['iCAT-v4 (제안)'][1]
sw = (dt.datetime.fromisoformat((M / 'mixO-onlinev4-rep1-x20' / 'phase-B-start.time').read_text().strip()).timestamp() - t0) / 3600
T = [r for r in csv.DictReader(open('/home/oy/iCAT/figs/data/fig7_v4_trace.csv', encoding='utf-8-sig')) if r['워크로드'] == 'OLTP → Varmail (10시간)']
def part(p):
    t = [r for r in T if r['파티션'] == p and r['구간 WAF']]
    x = [float(r['경과(분)']) / 60 for r in t]; act = [int(r['남은 후보 수']) for r in t]
    stt, swept = [], False   # 0 = sweep (until first elimination; again after a reset), 1 = search, 2 = settled
    for i, r in enumerate(t):
        if i and r['세대(재설정마다 +1)'] != t[i - 1]['세대(재설정마다 +1)']: swept = False
        elif i and act[i] < act[i - 1]: swept = True
        stt.append(2 if r['정착(1=예)'] == '1' else (1 if swept else 0))
    rs = [float(r['경과(분)']) / 60 for r in T if r['파티션'] == p and '재설정' in r['사건']]
    return x, act, stt, rs
P = {p: part(p) for p in '0123'}
x, act, stt, rs = P[PART]; X1 = max(x) + 0.1

# ---- PNG: left = 10 h in 10-min bins (60 points), right = switch zoom in 1-min bins; one partition only
BIG, SMALL = 10 / 60, 1 / 60
Z0, Z1 = sw - 0.1, sw + 0.6
def bins(lo, hi, step):
    w = {lab: binned(d, t0, step, lo, hi) for lab, d, *_ in pol}
    return w, bin_steps(x, stt, step, lo, hi, 'mode'), bin_steps(x, act, step, lo, hi, 'last')
VIEW = [(0, (0, X1 - 0.1), BIG), (1, (Z0, Z1), SMALL)]
fig, AX = plt.subplots(3, 2, figsize=(14, 7.8), gridspec_kw={'height_ratios': [1.25, 0.16, 0.9], 'width_ratios': [2.1, 1], 'hspace': 0.34, 'wspace': 0.08})
BINNED = {}
for col, (lo, hi), step in VIEW:
    ax = AX[:, col]; zoom = col == 1; w, sb, ab = bins(lo, hi, step); BINNED[col] = (w, sb, ab)
    for a_ in (ax[0], ax[2]): a_.axvspan(sw, hi + step, color='#f3f7fd', zorder=0, lw=0)
    for a_ in ax: a_.set_xlim(lo, hi); a_.axvline(sw, color=RED, lw=1.1, ls=(0, (3, 3)))
    for lab, d, c, lw in pol:
        ax[0].plot([h for h, _ in w[lab]], [v for _, v in w[lab]], color=c, lw=lw + 0.6, marker='o', ms=3.2, label=f'{lab}   10시간 전체 WAF {total(d):.3f}', zorder=3 if 'v4' in lab else 2)
    for h, s_ in sb: ax[1].axvspan(h - step / 2, h + step / 2, color=STATE[s_][1], lw=0)
    ax[1].set_yticks([]); ax[1].grid(False); ax[1].spines['bottom'].set_visible(False)
    ax[2].plot([h for h, _ in ab], [v for _, v in ab], color=V4, lw=2.2, drawstyle='steps-mid', marker='o', ms=3)
    ax[2].set_ylim(0, 50); ax[2].set_yticks([0, 15, 30, 45])
    for r_ in rs:
        for a_ in ax: a_.axvline(r_, color=PUR, lw=1.6)
    if zoom:
        for a_ in (ax[0], ax[2]): a_.set_yticklabels([])
        ax[0].set_title('전환 직후 확대 (1분 단위)', loc='left', fontsize=11, color=INK, weight='bold')
        ax[0].set_ylim(AX[0, 0].get_ylim()); ax[2].set_xlabel('측정 시작 후 시간 (시간)')
        lo_i = min(range(len(ab)), key=lambda i: ab[i][1] if sw <= ab[i][0] <= rs[0] + SMALL else 99)
        ax[2].annotate(f'전환 후 {ab[lo_i][1]}개까지 감소', ab[lo_i], (ab[lo_i][0] + 0.08, 6), fontsize=9.5, color=INK, va='center', arrowprops=dict(arrowstyle='->', color=INK2, lw=0.9))
        after = next(v for h, v in ab if h > rs[0] + 0.4)
        ax[2].annotate(f'변화 감지 → 재설정\n(전환 {(rs[0] - sw) * 60:.1f}분 뒤)\n다시 순회 후 {after}개', (rs[0], 30), (rs[0] + 0.07, 34), fontsize=9.5, color=PUR, weight='bold', va='center')
        ax[0].text(sw, 0.02, ' 전환', transform=ax[0].get_xaxis_transform(), fontsize=10, color=RED, weight='bold')
        ax[0].text(rs[0], 0.93, ' 재설정', transform=ax[0].get_xaxis_transform(), fontsize=10, color=PUR, weight='bold')
    else:
        ax[0].set_ylabel('구간 WAF (10분 단위)\n(낮을수록 좋음)'); ax[0].legend(loc='upper left', fontsize=9.5, frameon=False)
        ax[0].set_title('(가) 구간 WAF', loc='left', fontsize=11, color=INK, weight='bold')
        ax[0].text(sw / 2, 0.45, '앞 워크로드: OLTP', transform=ax[0].get_xaxis_transform(), ha='center', fontsize=11, color=INK2, weight='bold')
        ax[0].text((sw + hi) / 2, 0.45, '뒤 워크로드: Varmail', transform=ax[0].get_xaxis_transform(), ha='center', fontsize=11, color=V4, weight='bold')
        ax[0].text(sw, 0.02, f' 전환 {sw:.2f}시간', transform=ax[0].get_xaxis_transform(), fontsize=10, color=RED, weight='bold', va='bottom')
        ax[1].set_title('(나) 학습 상태 (10분마다 가장 오래 머문 상태)', loc='left', fontsize=11, color=INK, weight='bold')
        ax[2].set_ylabel('남은 후보 수'); ax[2].set_xlabel('측정 시작 후 시간 (시간)')
        ax[2].set_title('(다) 활성 후보 수 (각 10분 끝의 값)', loc='left', fontsize=11, color=INK, weight='bold')
        ax[0].axvspan(Z0, Z1, ymin=0, ymax=0.03, color=PUR, alpha=0.5, lw=0)
AX[1, 1].legend(handles=[Patch(color=c, label=n) for n, c in STATE], loc='lower right', bbox_to_anchor=(1.0, 1.05), ncol=3, fontsize=9.5, frameon=False, handlelength=1.2)
fig.suptitle('그림 7. OLTP → Varmail 10시간 실행에서 iCAT-v4의 학습 상태와 활성 후보 수 변화', x=0.06, ha='left', y=0.995, fontsize=13.5, weight='bold', color=INK)
fig.text(0.06, 0.95, 'OLTP 15분×20회 연속 + Varmail 5시간. 학습 기록은 4개 파티션 중 파티션 2. 왼쪽 10분 단위, 오른쪽은 전환 직후 1분 단위 확대.', fontsize=9.5, color=INK2)
for e in ('png', 'svg', 'pdf'): fig.savefig(f'/home/oy/iCAT/figs/fig7_10h.{e}', dpi=200, bbox_inches='tight')

# ---- xlsx: the same binned data (10-min bins over 10 h, and 1-min bins around the switch), partition 2 only
wb = Workbook(); ws = wb.active; ws.title = '그림7 10시간 (10분 단위)'; wz = wb.create_sheet('전환 직후 (1분 단위)')
def sheet(ws, col_i, unit):
    w, sb, ab = BINNED[col_i]; cols = []
    for lab, *_ in pol: cols += [(f'{lab} 시간(h)', [round(h, 4) for h, _ in w[lab]]), (f'{lab} {unit} 구간 WAF', [round(v, 4) for _, v in w[lab]])]
    cols += [('시간(h)', [round(h, 4) for h, _ in sb]), (f'학습 상태 p{PART} (0=순회,1=탐색,2=정착)', [v for _, v in sb])]
    cols += [('시간(h) ', [round(h, 4) for h, _ in ab]), (f'남은 후보 수 p{PART}', [v for _, v in ab])]
    for j, (h, v) in enumerate(cols, 1):
        ws.cell(row=1, column=j, value=h).font = Font(bold=True)
        for i, val in enumerate(v, 2): ws.cell(row=i, column=j, value=val)
    c0 = len(cols) + 2
    ws.cell(row=1, column=c0, value='전환(시간)').font = Font(bold=True); ws.cell(row=2, column=c0, value=round(sw, 3))
    ws.cell(row=3, column=c0, value=f'재설정(시간, p{PART})').font = Font(bold=True); ws.cell(row=4, column=c0, value=round(rs[0], 3) if rs else None)
    for i, (lab, d, *_) in enumerate(pol): ws.cell(row=6 + i, column=c0, value=f'{lab} 10시간 전체 WAF'); ws.cell(row=6 + i, column=c0 + 1, value=round(total(d), 3))
    L = ws.cell(row=1, column=c0 + 3).column_letter; lo, hi = VIEW[col_i][1]
    def chart(title, yt, ser, ymin, ymax, anchor, marker=True):
        ch = ScatterChart(); ch.title = title; ch.style = 13; ch.scatterStyle = 'lineMarker'; ch.display_blanks = 'span'
        ch.x_axis.title = '측정 시작 후 시간 (시간)'; ch.y_axis.title = yt; ch.height, ch.width = 9, 28; ch.legend.position = 'b'
        ch.x_axis.delete = False; ch.y_axis.delete = False; ch.x_axis.scaling.min = round(lo, 2); ch.x_axis.scaling.max = round(hi, 2)
        ch.x_axis.majorUnit = 1 if col_i == 0 else 0.1; ch.y_axis.scaling.min = ymin; ch.y_axis.scaling.max = ymax
        for xc, color, width in ser:
            n = len(cols[xc][1]); sr = Series(Reference(ws, min_col=xc + 2, min_row=1, max_row=n + 1), Reference(ws, min_col=xc + 1, min_row=2, max_row=n + 1), title_from_data=True)
            sr.smooth = False; sr.graphicalProperties.line.solidFill = color; sr.graphicalProperties.line.width = width
            sr.marker.symbol = 'circle' if marker else 'none'; sr.marker.size = 4; sr.marker.graphicalProperties.solidFill = color; sr.marker.graphicalProperties.line.solidFill = color
            ch.series.append(sr)
        ws.add_chart(ch, anchor)
    wafs = [v for lab, *_ in pol for _, v in w[lab]]; k = 2 * len(pol)
    chart(f'(가) OLTP → Varmail 10시간: {unit} 구간 WAF (낮을수록 좋음)', 'WAF', [(2 * i, c[1:].upper(), 22225) for i, (lab, d, c, lw) in enumerate(pol)], round(min(wafs) - 0.05, 1), round(max(wafs) + 0.05, 1), f'{L}2')
    chart(f'(나) 학습 상태 (0 = 전수 순회, 1 = 탐색, 2 = 정착)', '상태', [(k, '2A78D6', 22225)], -0.2, 2.2, f'{L}21')
    chart(f'(다) 활성 후보 수 (파티션 {PART})', '남은 후보 수', [(k + 2, '2A78D6', 28575)], 0, 48, f'{L}40')
sheet(ws, 0, '10분'); sheet(wz, 1, '1분')
wb.save('/home/oy/iCAT/figs/data/fig7_10h.xlsx')
print('policies drawn:', [lab for lab, *_ in pol], '| points left/right', len(BINNED[0][0]['iCAT-v4 (제안)']), len(BINNED[1][0]['iCAT-v4 (제안)']))
