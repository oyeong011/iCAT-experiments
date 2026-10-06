#!/usr/bin/env python3
"""v6 불규칙 순서 혼합 10시간(mixT) 그림 2개 + 엑셀.
그림 6: 20분 구간 WAF 추이 - CAT-37(기본) / CAT-50(견고) / CAT-47(최적) / iCAT-v6, 구간별 평균 WAF 표.
그림 7: v6가 학습했는지 - (가) v6 vs CAT-47 WAF, (나) 학습 상태, (다) 남은 후보 수 + 변화 감지(재설정) 시점.
-> figs/fig6_v6_mixT.(png|pdf), figs/fig7_v6_mixT.(png|pdf), figs/data/fig6_v6_mixT.xlsx, figs/data/fig7_v6_mixT.xlsx
원천: control-series.txt, phase-X-start.time, summary.txt, kernel 로그(analysis/v4-log.py). v6 = 두 번째 PC(icat-2) 실행."""
import re, datetime as dt, importlib.util
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch
from openpyxl import Workbook
from openpyxl.chart import ScatterChart, BarChart, Reference, Series
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.legend import LegendEntry
from openpyxl.styles import Font, PatternFill, Alignment
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
spec = importlib.util.spec_from_file_location('v4log', '/home/oy/iCAT/analysis/v4-log.py'); v4log = importlib.util.module_from_spec(spec); spec.loader.exec_module(v4log)
R = Path('/home/oy/iCAT/result'); M = R / 'mix-20260911'; FIG = Path('/home/oy/iCAT/figs')
V6 = R / 'v6-mixT-20261005' / 'mixT-onlinev6-rep1'
# (label, dir, color, line width) - drawn in this order, v6 last so it sits on top
POL = [('CAT-37 (기본)', R / 'mixT-fixed37-tenhour-20261004' / 'mixT-fixed37-rep1', '#e3a33b', 1.5),
       ('CAT-50 (견고)', R / 'mixT-fixed50-tenhour-20261004' / 'mixT-fixed50-rep1', '#9a9994', 1.5),
       ('CAT-47 (최적)', M / 'mixT-fixed47-rep1', '#2b2a28', 1.5),
       ('iCAT-v6 (제안)', V6, '#2a78d6', 2.6)]
PART, STEP = '2', 20 / 60          # 20-min bins: 30 points per line instead of 60
NAMES = ['YCSB-A', 'OLTP', 'Varmail', 'YCSB-A', 'YCSB-B', 'FIO-Fast', 'Varmail', 'YCSB-A', 'OLTP']
TYPE = {'YCSB-A': 'SQLite DB\n읽기50·수정50', 'YCSB-B': 'SQLite DB\n읽기95·수정5', 'OLTP': 'DB 서버 흉내\n(Filebench)',
        'Varmail': '메일 서버 흉내\n(Filebench)', 'FIO-Fast': '합성 덮어쓰기\n(FIO 3영역)'}
BAND = {'YCSB-A': '#f6f1e7', 'YCSB-B': '#f3ece0', 'OLTP': '#eaf3ee', 'Varmail': '#eef2fb', 'FIO-Fast': '#f7ecec'}
INK, INK2, BLUE, PUR = '#1d1d1f', '#6e6e73', '#2a78d6', '#7d3cff'
STATE = [('전수 순회', '#d9d9de'), ('탐색', '#8e8e93'), ('정착', BLUE)]
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 10.5, 'axes.facecolor': 'white', 'figure.facecolor': 'white',
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False, 'axes.edgecolor': '#d2d2d7',
                     'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': '#ededf0', 'grid.linewidth': 0.8, 'axes.axisbelow': True,
                     'xtick.color': INK2, 'ytick.color': INK2, 'ytick.left': False, 'axes.labelcolor': INK2})

def run(d):   # STEP-bin WAF on the run's own clock, phase starts (h), totals, per-phase WAF
    raw = [tuple(map(int, m.groups())) for l in open(d / 'control-series.txt') if (m := re.match(r'(\d+) .*active=1 .*host_pages=(\d+) gc_pages=(\d+)', l))]
    t0 = raw[0][0]; s = [((t - t0) / 3600, h, g) for t, h, g in raw]
    out, k = [], 0.0
    while k + STEP <= s[-1][0] + 1e-9:
        a = min(s, key=lambda p: abs(p[0] - k)); b = min(s, key=lambda p: abs(p[0] - k - STEP))
        if b[1] > a[1]: out.append((round(k + STEP / 2, 4), 1 + (b[2] - a[2]) / (b[1] - a[1])))
        k += STEP
    starts = [(dt.datetime.fromisoformat((d / f'phase-{c}-start.time').read_text().strip()).timestamp() - t0) / 3600 for c in 'ABCDEFGHI']
    sm = (d / 'summary.txt').read_text()
    tot = float(re.search(r'^total .*WAF=([\d.]+)', sm, re.M)[1])
    ph = [float(re.search(rf'^phase{c}\(\S+\) .*WAF=([\d.]+)', sm, re.M)[1]) for c in 'ABCDEFGHI']
    return out, starts, tot, ph, s[-1][0]
D = {lab: run(d) for lab, d, *_ in POL}
_, starts, V6T, V6PH, X1 = D['iCAT-v6 (제안)']
bounds = starts + [X1]
mids = [(bounds[i] + bounds[i + 1]) / 2 for i in range(len(NAMES))]

# v6 learner trace, partition PART (same log format as v4; v6 adds "WATGC_V6 shift-reset" before each reset)
L = v4log.lines(str(V6))
ts = lambda l: float(re.match(r'\[\s*(\d+\.\d+)\]', l)[1])
t0 = next(ts(l) for l in L if 'Measurement: command=start' in l)
tr = [((ts(l) - t0) / 3600, int(m[1]), int(m[2]), int(m[3])) for l in L if (m := re.search(rf'part={PART} epoch=(\d+) window=\d+ .*?settled=(\d) active=(\d+)', l))]
resets = [(ts(l) - t0) / 3600 for l in L if 'WATGC_V2 reset' in l and f'part={PART} ' in l]
stt, swept = [], False
for i, (h, ep, st_, act) in enumerate(tr):
    if i and ep != tr[i - 1][1]: swept = False
    elif i and act < tr[i - 1][3]: swept = True
    stt.append(2 if st_ else (1 if swept else 0))
LSTEP = 10 / 60
def bin_last(vals):   # per 10-min bin: last value (candidates) / longest-held state
    out, k = [], 0.0
    while k + LSTEP <= X1 + 1e-9:
        idx = [i for i, r in enumerate(tr) if k <= r[0] < k + LSTEP]
        if idx: out.append((round(k + LSTEP / 2, 4), vals(idx)))
        k += LSTEP
    return out
cand = bin_last(lambda idx: tr[idx[-1]][3])
state = bin_last(lambda idx: max(set(stt[i] for i in idx), key=[stt[i] for i in idx].count))
settled_share = [sum(1 for h, s_ in state if bounds[i] <= h < bounds[i + 1] and s_ == 2) / max(1, sum(1 for h, _ in state if bounds[i] <= h < bounds[i + 1])) for i in range(len(NAMES))]
NOTE = 'CAT-37·50은 DB 300k 레코드(나머지는 250k). 정책마다 1회 실행. v6·CAT-37·50 = 두 번째 PC, CAT-47 = 이 PC.'

# ---------------- PNG (check images)
def bands(a, top=True):
    for i, n in enumerate(NAMES):
        a.axvspan(bounds[i], bounds[i + 1], color=BAND[n], lw=0, zorder=0)
        if i: a.axvline(bounds[i], color='#5a5955', lw=1.1, ls=(0, (4, 3)), zorder=1)
        if top:
            a.text(mids[i], 1.13, f'{i + 1}. {n}', transform=a.get_xaxis_transform(), ha='center', va='bottom', fontsize=9.5, color=INK, weight='bold')
            a.text(mids[i], 1.01, TYPE[n], transform=a.get_xaxis_transform(), ha='center', va='bottom', fontsize=7.8, color=INK2, linespacing=1.15)
f6, a6 = plt.subplots(figsize=(14, 5.6)); bands(a6)
for lab, d, c, lw in POL:
    w, _, tot, *_ = D[lab]
    gap = '' if 'v6' in lab else f'  (v6 {(V6T / tot - 1) * 100:+.1f}%)'
    a6.plot([h for h, _ in w], [v for _, v in w], color=c, lw=lw, label=f'{lab}   10시간 전체 {tot:.3f}{gap}', zorder=3 if 'v6' in lab else 2)
a6.set_xlim(0, X1); a6.set_xticks(range(0, int(X1) + 1)); a6.set_xlabel('측정 시작 후 시간 (시간)'); a6.set_ylabel('구간 WAF (20분 단위, 낮을수록 좋음)')
a6.legend(loc='upper center', bbox_to_anchor=(0.5, -0.13), ncol=2, fontsize=9.5, frameon=False)
f6.subplots_adjust(top=0.74)
f6.suptitle('그림 6. 불규칙 순서 응용 혼합 10시간: iCAT-v6 vs 최적·견고·기본 CAT의 WAF 추이', x=0.06, ha='left', y=0.985, fontsize=13.5, weight='bold', color=INK)
f6.text(0.06, 0.93, '점선 = 워크로드 전환. 각 선 = 20분 동안의 WAF. 범례 괄호 = 그 정책 대비 v6의 차이(음수 = v6가 낮음). ' + NOTE, fontsize=9, color=INK2)
for e in ('png', 'pdf'): f6.savefig(FIG / f'fig6_v6_mixT.{e}', dpi=200, bbox_inches='tight')

ref = 'CAT-47 (최적)'
f7, ax = plt.subplots(3, 1, figsize=(14, 8.2), sharex=True, gridspec_kw={'height_ratios': [1.2, 0.16, 0.9], 'hspace': 0.3})
bands(ax[0]); bands(ax[2], top=False)
for lab, d, c, lw in POL:
    if lab in (ref, 'iCAT-v6 (제안)'):
        w, _, tot, *_ = D[lab]; ax[0].plot([h for h, _ in w], [v for _, v in w], color=c, lw=lw, label=f'{lab}   10시간 전체 {tot:.3f}')
ax[0].set_ylabel('구간 WAF (20분)\n(낮을수록 좋음)'); ax[0].legend(loc='upper left', fontsize=9.5, frameon=True, facecolor='white', edgecolor='#e0dfdb')
ax[0].set_title('(가) WAF: v6 vs 최적 고정값', loc='left', fontsize=11, color=INK, weight='bold', pad=52)
for h, s_ in state: ax[1].axvspan(h - LSTEP / 2, h + LSTEP / 2, color=STATE[s_][1], lw=0)
ax[1].set_yticks([]); ax[1].grid(False); ax[1].set_title(f'(나) v6 학습 상태 (파티션 {PART}, 10분마다 가장 오래 머문 상태)', loc='left', fontsize=10.5, color=INK2)
ax[1].legend(handles=[Patch(color=c, label=n) for n, c in STATE], loc='lower right', bbox_to_anchor=(1.0, 1.0), ncol=3, fontsize=9, frameon=False, handlelength=1.0)
ax[2].plot([h for h, _ in cand], [v for _, v in cand], color=BLUE, lw=2.2, drawstyle='steps-mid')
for r in resets:
    for a_ in ax: a_.axvline(r, color=PUR, lw=1.6, zorder=4)
ax[2].text(resets[0] + 0.05, 50, '보라 선 = 변화 감지 → 재설정', fontsize=9, color=PUR, weight='bold', va='top')
ax[2].set_ylim(0, 62); ax[2].set_yticks([0, 15, 30, 45, 60]); ax[2].set_ylabel('남은 후보 수'); ax[2].set_xlabel('측정 시작 후 시간 (시간)')
ax[2].set_title(f'(다) v6 남은 후보 수 (파티션 {PART}, 45개에서 시작, 줄어들면 = 좋은 후보로 좁혀 가는 중)', loc='left', fontsize=10.5, color=INK2)
ax[2].set_xlim(0, X1); ax[2].set_xticks(range(0, int(X1) + 1))
f7.subplots_adjust(top=0.80)
f7.suptitle('그림 7. 불규칙 순서 응용 혼합 10시간에서 iCAT-v6가 학습했는지: WAF, 학습 상태, 남은 후보 수', x=0.06, ha='left', y=0.985, fontsize=13.5, weight='bold', color=INK)
f7.text(0.06, 0.945, f'9구간 각 4000초. 보라 선 = v6가 워크로드 변화를 감지해 처음부터 다시 배운 시점(파티션 {PART}, {len(resets)}번). ' + NOTE, fontsize=9, color=INK2)
for e in ('png', 'pdf'): f7.savefig(FIG / f'fig7_v6_mixT.{e}', dpi=200, bbox_inches='tight')

# ---------------- xlsx
HDR = PatternFill('solid', fgColor='EEF2FB')
def put(ws, r, c, v, bold=False, fmt=None):
    x = ws.cell(row=r, column=c, value=v)
    if bold: x.font = Font(bold=True); x.fill = HDR; x.alignment = Alignment(wrap_text=True, vertical='center')
    if fmt: x.number_format = fmt
    return x
def table(ws, c0, cols):   # cols = [(header, values)] written from row 1
    for j, (h, v) in enumerate(cols, c0):
        put(ws, 1, j, h, True); ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = 13
        for i, val in enumerate(v, 2): put(ws, i, j, val, fmt='0.000' if isinstance(val, float) else None)
def helpers(ws, c0, ytop, ybot):
    """switch lines (2 rows each) + one label point per phase at ytop; returns column map"""
    for i in range(1, len(NAMES)):
        c = c0 + 2 * (i - 1); put(ws, 1, c, f'전환{i} 시간', True); put(ws, 1, c + 1, f'전환{i}', True)
        for r, y in ((2, ybot), (3, ytop)): put(ws, r, c, round(bounds[i], 3)); put(ws, r, c + 1, y)
    lc = c0 + 2 * (len(NAMES) - 1)
    for i, n in enumerate(NAMES):
        put(ws, 1, lc + 2 * i, f'라벨{i + 1} 시간', True); put(ws, 1, lc + 2 * i + 1, f'{i + 1}.{n}', True)
        put(ws, 2, lc + 2 * i, round(mids[i], 3)); put(ws, 2, lc + 2 * i + 1, ytop)
    return lc
def chart(ws, title, ytitle, ser, ymin, ymax, c0, lc, anchor, h=11, w=32):
    ch = ScatterChart(); ch.title = title; ch.style = 13; ch.scatterStyle = 'lineMarker'
    ch.x_axis.title = '측정 시작 후 시간 (시간)'; ch.y_axis.title = ytitle; ch.height, ch.width = h, w; ch.legend.position = 'b'
    ch.x_axis.delete = False; ch.y_axis.delete = False; ch.x_axis.scaling.min = 0; ch.x_axis.scaling.max = 10; ch.x_axis.majorUnit = 1
    ch.y_axis.scaling.min = ymin; ch.y_axis.scaling.max = ymax; ch.y_axis.majorGridlines = ch.y_axis.majorGridlines; ch.x_axis.majorGridlines = None
    for xc, n, color, width, marker in ser:
        s = Series(Reference(ws, min_col=xc + 1, min_row=1, max_row=n + 1), Reference(ws, min_col=xc, min_row=2, max_row=n + 1), title_from_data=True)
        s.smooth = False; s.graphicalProperties.line.solidFill = color; s.graphicalProperties.line.width = width
        if not width: s.graphicalProperties.line.noFill = True
        s.marker.symbol = marker
        if marker != 'none': s.marker.size = 4 if width else 9; s.marker.graphicalProperties.solidFill = color; s.marker.graphicalProperties.line.solidFill = color
        ch.series.append(s)
    hidden = []
    for i in range(1, len(NAMES)):   # dashed vertical line at each workload switch
        c = c0 + 2 * (i - 1)
        s = Series(Reference(ws, min_col=c + 1, min_row=1, max_row=3), Reference(ws, min_col=c, min_row=2, max_row=3), title_from_data=True)
        s.smooth = False; s.marker.symbol = 'none'; s.graphicalProperties.line.solidFill = '8A8984'; s.graphicalProperties.line.dashStyle = 'dash'; s.graphicalProperties.line.width = 12700
        hidden.append(len(ch.series)); ch.series.append(s)
    for i in range(len(NAMES)):      # phase name written above each phase (one invisible point, label = series name)
        c = lc + 2 * i
        s = Series(Reference(ws, min_col=c + 1, min_row=1, max_row=2), Reference(ws, min_col=c, min_row=2, max_row=2), title_from_data=True)
        s.marker.symbol = 'none'; s.graphicalProperties.line.noFill = True
        s.dLbls = DataLabelList(); s.dLbls.showSerName = True; s.dLbls.showVal = False; s.dLbls.showLegendKey = False; s.dLbls.position = 't'
        hidden.append(len(ch.series)); ch.series.append(s)
    ch.legend.legendEntry = [LegendEntry(idx=i, delete=True) for i in hidden]
    ws.add_chart(ch, anchor)

# ---- Fig.6 workbook
wb = Workbook(); ws = wb.active; ws.title = '그림6 WAF 추이'
cols = []
for lab, *_ in POL: w = D[lab][0]; cols += [(f'{lab} 시간(h)', [h for h, _ in w]), (f'{lab} 10시간 전체 {D[lab][2]:.3f}', [round(v, 4) for _, v in w])]
table(ws, 1, cols)
allw = [v for lab in D for _, v in D[lab][0]]; ymax = round(max(allw) + 0.5, 0)
lc = helpers(ws, len(cols) + 2, ymax - 0.15, 0.9)
ser = [(2 * i + 1, len(D[lab][0]), c[1:].upper(), 34925 if 'v6' in lab else 19050, 'none') for i, (lab, d, c, lw) in enumerate(POL)]
anchor = ws.cell(row=1, column=lc + 2 * len(NAMES) + 1).column_letter
chart(ws, '그림 6. 불규칙 순서 응용 혼합 10시간: 20분 구간 WAF 추이 (낮을수록 좋음)', 'WAF', ser, 0.9, ymax, len(cols) + 2, lc, f'{anchor}2', h=13, w=34)
put(ws, 33, len(cols) + 2, '점선 = 워크로드 전환, 위 글자 = 그 구간의 워크로드. ' + NOTE)

ws2 = wb.create_sheet('구간별 WAF')   # per-phase table + clustered bar chart
hdr = ['구간', '워크로드', '종류'] + [lab for lab, *_ in POL] + ['v6 vs 최적(%)', 'v6 vs 기본(%)']
for j, h in enumerate(hdr, 1): put(ws2, 1, j, h, True)
for i, n in enumerate(NAMES):
    row = [f'{i + 1}. {n}', n, TYPE[n].replace('\n', ' ')] + [round(D[lab][3][i], 3) for lab, *_ in POL]
    row += [round((V6PH[i] / D['CAT-47 (최적)'][3][i] - 1) * 100, 1), round((V6PH[i] / D['CAT-37 (기본)'][3][i] - 1) * 100, 1)]
    for j, v in enumerate(row, 1): put(ws2, 2 + i, j, v)
row = ['10시간 전체', '', ''] + [round(D[lab][2], 3) for lab, *_ in POL] + [round((V6T / D['CAT-47 (최적)'][2] - 1) * 100, 1), round((V6T / D['CAT-37 (기본)'][2] - 1) * 100, 1)]
for j, v in enumerate(row, 1): put(ws2, 11, j, v, bold=True)
for j, wdt in enumerate([12, 10, 22, 13, 13, 13, 14, 13, 13], 1): ws2.column_dimensions[ws2.cell(row=1, column=j).column_letter].width = wdt
bc = BarChart(); bc.type = 'col'; bc.grouping = 'clustered'; bc.title = '구간별 평균 WAF (낮을수록 좋음)'; bc.y_axis.title = 'WAF'
bc.add_data(Reference(ws2, min_col=4, max_col=7, min_row=1, max_row=11), titles_from_data=True); bc.set_categories(Reference(ws2, min_col=1, min_row=2, max_row=11))
for s, (lab, d, c, lw) in zip(bc.series, POL): s.graphicalProperties.solidFill = c[1:].upper(); s.graphicalProperties.line.noFill = True
bc.height, bc.width = 11, 30; bc.legend.position = 'b'; bc.x_axis.delete = False; bc.y_axis.delete = False; bc.y_axis.scaling.min = 0.8
ws2.add_chart(bc, 'A14')
put(ws2, 13, 1, '음수(%) = v6의 WAF가 더 낮음(좋음). ' + NOTE)
wb.save(FIG / 'data' / 'fig6_v6_mixT.xlsx')

# ---- Fig.7 workbook
wb = Workbook(); ws = wb.active; ws.title = '그림7 v6 학습'
cols = []
for lab in (ref, 'iCAT-v6 (제안)'): w = D[lab][0]; cols += [(f'{lab} 시간(h)', [h for h, _ in w]), (f'{lab} WAF', [round(v, 4) for _, v in w])]
cols += [('시간(h)', [h for h, _ in state]), (f'학습 상태 p{PART} (0=순회 1=탐색 2=정착)', [v for _, v in state])]
cols += [('시간(h) ', [h for h, _ in cand]), (f'남은 후보 수 p{PART}', [v for _, v in cand])]
cols += [('재설정 시간(h)', [round(r, 3) for r in resets]), ('재설정', [58] * len(resets))]
table(ws, 1, cols)
c0 = len(cols) + 2; anchor = ws.cell(row=1, column=c0 + 4 * len(NAMES) + 1).column_letter
# helper columns per chart: each panel has its own y range, so three helper blocks
lcA = helpers(ws, c0, round(max(allw) + 0.35, 1), 0.9)
wa = ws.cell(row=1, column=c0).column_letter
chart(ws, '(가) WAF: v6 vs 최적 고정값 CAT-47 (20분 구간, 낮을수록 좋음)', 'WAF', [(1, len(D[ref][0]), '2B2A28', 19050, 'none'), (3, len(D['iCAT-v6 (제안)'][0]), '2A78D6', 34925, 'none')],
      0.9, round(max(allw) + 0.5, 1), c0, lcA, f'{anchor}2')
ws2 = wb.create_sheet('학습 그래프 보조')   # second/third panels get their own helper columns (different y ranges)
def copy_cols(dst, src_cols):
    for j, (h, v) in enumerate(src_cols, 1):
        put(dst, 1, j, h, True)
        for i, val in enumerate(v, 2): put(dst, i, j, val)
copy_cols(ws2, cols)
lcB = helpers(ws2, c0, 2.15, -0.2)
chart(ws2, '(나) v6 학습 상태 (0 = 전수 순회, 1 = 탐색, 2 = 정착)', '상태', [(5, len(state), '2A78D6', 22225, 'circle')], -0.2, 2.4, c0, lcB, 'A2', h=9)
ws3 = wb.create_sheet('후보 수 보조'); copy_cols(ws3, cols)
lcC = helpers(ws3, c0, 61, 0)
chart(ws3, f'(다) v6 남은 후보 수 (파티션 {PART}) + 보라 점 = 변화 감지 후 재설정', '남은 후보 수', [(7, len(cand), '2A78D6', 28575, 'none'), (9, len(resets), '7D3CFF', 0, 'diamond')], 0, 64, c0, lcC, 'A2', h=10)
# put panels (나)(다) on the main sheet too, by moving the chart objects
for src, row in ((ws2, 25), (ws3, 45)):
    chx = src._charts.pop(); chx.anchor = f'{anchor}{row}'; ws._charts.append(chx)
put(ws, len(state) + 4, 1, f'보라 = 변화 감지 → 처음부터 다시 학습 (파티션 {PART}, {len(resets)}번). ' + NOTE)
wb.save(FIG / 'data' / 'fig7_v6_mixT.xlsx')
print('totals', {l: round(D[l][2], 3) for l in D}, '| resets h', [round(r, 2) for r in resets])
print('settled share per phase', [round(x, 2) for x in settled_share])
