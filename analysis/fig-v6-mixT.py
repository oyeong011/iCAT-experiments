#!/usr/bin/env python3
"""v6 불규칙 순서 혼합 10시간(mixT) 그림 2개 + 엑셀.
그림 6: 20분 구간 WAF 추이 - CAT-37(기본) / CAT-50(견고) / CAT-47(최적) / iCAT-v6, 구간별 평균 WAF 표.
그림 7: v6가 후보를 줄여 가며 학습했는지 - (가) 10시간 동안 남은 후보 수(판단마다 1점, 재설정 표시),
        (나) 학습 회차별 곡선: 재설정 후 판단 횟수 vs 남은 후보 수 (45개 전부 한 번씩 시험 -> 나쁜 후보 제거).
-> figs/fig6_v6_mixT.(png|pdf), figs/fig7_v6_mixT.(png|pdf), figs/data/fig6_v6_mixT.xlsx, figs/data/fig7_v6_mixT.xlsx
원천: control-series.txt, phase-X-start.time, summary.txt, kernel 로그(analysis/v4-log.py). v6 = 두 번째 PC(icat-2) 실행."""
import re, datetime as dt, importlib.util
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
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
PART, STEP, MAXJ = '2', 20 / 60, 250   # 20-min WAF bins; learning curves shown for the first MAXJ judgments
NAMES = ['YCSB-A', 'OLTP', 'Varmail', 'YCSB-A', 'YCSB-B', 'FIO-Fast', 'Varmail', 'YCSB-A', 'OLTP']
TYPE = {'YCSB-A': 'SQLite DB\n읽기50·수정50', 'YCSB-B': 'SQLite DB\n읽기95·수정5', 'OLTP': 'DB 서버 흉내\n(Filebench)',
        'Varmail': '메일 서버 흉내\n(Filebench)', 'FIO-Fast': '합성 덮어쓰기\n(FIO 3영역)'}
BAND = {'YCSB-A': '#f6f1e7', 'YCSB-B': '#f3ece0', 'OLTP': '#eaf3ee', 'Varmail': '#eef2fb', 'FIO-Fast': '#f7ecec'}
INK, INK2, BLUE, PUR = '#1d1d1f', '#6e6e73', '#2a78d6', '#7d3cff'
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

# v6 learner trace, partition PART: one sample line per judgment (window). epoch = learning round (new round after each reset)
L = v4log.lines(str(V6))
ts = lambda l: float(re.match(r'\[\s*(\d+\.\d+)\]', l)[1])
t0 = next(ts(l) for l in L if 'Measurement: command=start' in l)
tr = [((ts(l) - t0) / 3600, int(m[1]), int(m[2])) for l in L if (m := re.search(rf'part={PART} epoch=(\d+) window=\d+ .*?active=(\d+)', l))]
resets = [(ts(l) - t0) / 3600 for l in L if 'WATGC_V2 reset' in l and f'part={PART} ' in l]
rounds = []   # (round no., start h, end h, workloads it overlapped, candidate counts per judgment)
for ep in sorted({e for _, e, _ in tr}):
    v = [(h, a) for h, e, a in tr if e == ep]
    h0, h1 = v[0][0], v[-1][0]
    wl = [f'{i + 1}.{n}' for i, n in enumerate(NAMES) if min(h1, bounds[i + 1]) - max(h0, bounds[i]) > 0.25]   # ignore overlaps under 15 min
    rounds.append((ep, h0, h1, wl, [a for _, a in v]))
NARROW = {'FIO-Fast', 'Varmail'}   # rounds that end with few candidates get a strong color, the rest gray
RCOL = ['#c9c8c3', '#b4b3ae', '#8a8984', '#d9534f', '#2a78d6', '#5a5955', '#e0dfdb']
def rlabel(r): ep, h0, h1, wl, a = r; return f'{ep}회차 ({h0:.1f}~{h1:.1f}h, {"+".join(wl)})  {a[0]}→{a[-1]}개'
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
    a6.plot([h for h, _ in w], [v for _, v in w], color=c, lw=lw, marker='o', ms=4.5 if 'v6' in lab else 3.5,
            label=f'{lab}   10시간 전체 {tot:.3f}{gap}', zorder=3 if 'v6' in lab else 2)
a6.set_xlim(0, X1); a6.set_xticks(range(0, int(X1) + 1)); a6.set_xlabel('측정 시작 후 시간 (시간)'); a6.set_ylabel('구간 WAF (20분 단위, 낮을수록 좋음)')
a6.legend(loc='upper center', bbox_to_anchor=(0.5, -0.13), ncol=2, fontsize=9.5, frameon=False)
f6.subplots_adjust(top=0.74)
f6.suptitle('그림 6. 불규칙 순서 응용 혼합 10시간: iCAT-v6 vs 최적·견고·기본 CAT의 WAF 추이', x=0.06, ha='left', y=0.985, fontsize=13.5, weight='bold', color=INK)
f6.text(0.06, 0.93, '점선 = 워크로드 전환. 각 점 = 20분 동안의 WAF. 범례 괄호 = 그 정책 대비 v6의 차이(음수 = v6가 낮음). ' + NOTE, fontsize=9, color=INK2)
for e in ('png', 'pdf'): f6.savefig(FIG / f'fig6_v6_mixT.{e}', dpi=200, bbox_inches='tight')

f7, ax = plt.subplots(2, 1, figsize=(14, 9.4), gridspec_kw={'height_ratios': [1, 1.15], 'hspace': 0.42})
bands(ax[0])
ax[0].plot([h for h, _, _ in tr], [a for _, _, a in tr], color=BLUE, lw=1.6, drawstyle='steps-post', marker='o', ms=2.2, zorder=3)
for r in resets: ax[0].axvline(r, color=PUR, lw=1.6, zorder=4)
for ep, h0, h1, wl, a in rounds:   # how far each round narrowed, written at its lowest point
    lo = min(a)
    if lo == a[0]: continue   # nothing removed: no label
    hl = next(h for h, e, x in tr if e == ep and x == lo)
    ax[0].annotate(f'{a[0]}→{lo}', (hl, lo), (4, -14 if lo > 20 else 6), textcoords='offset points', fontsize=9.5, color=BLUE, weight='bold')
ax[0].set_ylim(0, 50); ax[0].set_yticks([0, 15, 30, 45]); ax[0].set_ylabel('남은 후보 수'); ax[0].set_xlabel('측정 시작 후 시간 (시간)')
ax[0].set_xlim(0, X1); ax[0].set_xticks(range(0, int(X1) + 1))
ax[0].set_title(f'(가) 10시간 동안 v6의 남은 후보 수 (파티션 {PART}, 점 1개 = 판단 1번). 보라 선 = 변화 감지 → 45개로 되돌리고 다시 학습', loc='left', fontsize=11, color=INK, weight='bold', pad=52)
for r, c in zip(rounds, RCOL):
    a = r[4][:MAXJ]; strong = any(w.split('.')[1] in NARROW for w in r[3]) and min(a) <= 10
    ax[1].plot(range(1, len(a) + 1), a, color=c, lw=2.6 if strong else 1.5, marker='o', ms=3.2 if strong else 2.4, markevery=5 if len(a) > 60 else 1,
               label=rlabel(r), zorder=3 if strong else 2)
ax[1].axvspan(0, 45, color='#f4f4f6', lw=0, zorder=0)
ax[1].text(22.5, 40, '① 45개를 한 번씩 다 시험\n(아직 아무것도 안 버림)', ha='center', va='top', fontsize=9.5, color=INK2)
ax[1].text(52, 30, '② 나쁜 후보를 버림\n→ 좋은 5개만 남음', ha='left', va='center', fontsize=9.5, color='#d9534f', weight='bold')
ax[1].set_xlim(0, MAXJ); ax[1].set_ylim(0, 50); ax[1].set_yticks([0, 5, 15, 30, 45]); ax[1].set_ylabel('남은 후보 수')
ax[1].set_xlabel(f'재설정 후 판단 횟수 (처음 {MAXJ}번)')
ax[1].set_title('(나) 학습 회차별로 겹쳐 보기: 판단이 쌓일수록 후보가 줄면 = 학습', loc='left', fontsize=11, color=INK, weight='bold')
ax[1].legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=9, frameon=False)
f7.subplots_adjust(top=0.82)
f7.suptitle('그림 7. 불규칙 순서 응용 혼합 10시간에서 iCAT-v6가 후보를 줄여 가며 학습했는지', x=0.06, ha='left', y=0.985, fontsize=13.5, weight='bold', color=INK)
f7.text(0.06, 0.935, 'GC 후보 설정 45개 중 좋은 것을 찾는 과정. 6번 FIO-Fast와 7번 Varmail에서는 45→5로 좁혔다. YCSB·OLTP와 3번 Varmail에서는 후보끼리 차이가 작아 거의 안 줄었다.\n' + NOTE,
         fontsize=9, color=INK2, wrap=True)
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
def helpers(ws, c0, ytop, ybot, lines=None):
    """vertical lines (2 rows each; default = workload switches) + one label point per phase at ytop"""
    lines = lines or [(f'전환{i}', bounds[i]) for i in range(1, len(NAMES))]
    for i, (nm, x) in enumerate(lines):
        c = c0 + 2 * i; put(ws, 1, c, f'{nm} 시간', True); put(ws, 1, c + 1, nm, True)
        for r, y in ((2, ybot), (3, ytop)): put(ws, r, c, round(x, 3)); put(ws, r, c + 1, y)
    lc = c0 + 2 * len(lines)
    for i, n in enumerate(NAMES):
        put(ws, 1, lc + 2 * i, f'라벨{i + 1} 시간', True); put(ws, 1, lc + 2 * i + 1, f'{i + 1}.{n}', True)
        put(ws, 2, lc + 2 * i, round(mids[i], 3)); put(ws, 2, lc + 2 * i + 1, ytop)
    return lc, len(lines)
def scatter(title, xt, yt, h, w, xmin, xmax, xunit, ymin, ymax):
    ch = ScatterChart(); ch.title = title; ch.style = 13; ch.scatterStyle = 'lineMarker'
    ch.x_axis.title = xt; ch.y_axis.title = yt; ch.height, ch.width = h, w; ch.legend.position = 'b'
    ch.x_axis.delete = False; ch.y_axis.delete = False; ch.x_axis.scaling.min = xmin; ch.x_axis.scaling.max = xmax; ch.x_axis.majorUnit = xunit
    ch.y_axis.scaling.min = ymin; ch.y_axis.scaling.max = ymax; ch.x_axis.majorGridlines = None
    return ch
def add(ch, ws, xc, n, color, width, marker, msize=4, r0=2):
    s = Series(Reference(ws, min_col=xc + 1, min_row=1, max_row=n + 1), Reference(ws, min_col=xc, min_row=r0, max_row=n + 1), title_from_data=True)
    s.smooth = False; s.graphicalProperties.line.solidFill = color; s.graphicalProperties.line.width = width
    s.marker.symbol = marker
    if marker != 'none': s.marker.size = msize; s.marker.graphicalProperties.solidFill = color; s.marker.graphicalProperties.line.solidFill = color
    ch.series.append(s)
def decorate(ch, ws, c0, lc, nlines, lcolor='8A8984'):   # vertical lines + phase names above, hidden from the legend
    hidden = []
    for i in range(nlines):
        c = c0 + 2 * i
        s = Series(Reference(ws, min_col=c + 1, min_row=1, max_row=3), Reference(ws, min_col=c, min_row=2, max_row=3), title_from_data=True)
        s.smooth = False; s.marker.symbol = 'none'; s.graphicalProperties.line.solidFill = lcolor; s.graphicalProperties.line.width = 12700
        if lcolor == '8A8984': s.graphicalProperties.line.dashStyle = 'dash'
        hidden.append(len(ch.series)); ch.series.append(s)
    for i in range(len(NAMES)):
        c = lc + 2 * i
        s = Series(Reference(ws, min_col=c + 1, min_row=1, max_row=2), Reference(ws, min_col=c, min_row=2, max_row=2), title_from_data=True)
        s.marker.symbol = 'none'; s.graphicalProperties.line.noFill = True
        s.dLbls = DataLabelList(); s.dLbls.showSerName = True; s.dLbls.showVal = False; s.dLbls.showLegendKey = False; s.dLbls.position = 't'
        hidden.append(len(ch.series)); ch.series.append(s)
    ch.legend.legendEntry = [LegendEntry(idx=i, delete=True) for i in hidden]

# ---- Fig.6 workbook
wb = Workbook(); ws = wb.active; ws.title = '그림6 WAF 추이'
cols = []
for lab, *_ in POL: w = D[lab][0]; cols += [(f'{lab} 시간(h)', [h for h, _ in w]), (f'{lab} 10시간 전체 {D[lab][2]:.3f}', [round(v, 4) for _, v in w])]
table(ws, 1, cols)
allw = [v for lab in D for _, v in D[lab][0]]; ymax = round(max(allw) + 0.5, 0)
c0 = len(cols) + 2; lc, nl = helpers(ws, c0, ymax - 0.15, 0.9)
ch = scatter('그림 6. 불규칙 순서 응용 혼합 10시간: 20분 구간 WAF 추이 (낮을수록 좋음)', '측정 시작 후 시간 (시간)', 'WAF', 13, 34, 0, 10, 1, 0.9, ymax)
for i, (lab, d, c, lw) in enumerate(POL):
    v6 = 'v6' in lab; add(ch, ws, 2 * i + 1, len(D[lab][0]), c[1:].upper(), 34925 if v6 else 19050, 'circle', 6 if v6 else 4)
decorate(ch, ws, c0, lc, nl)
ws.add_chart(ch, f'{ws.cell(row=1, column=lc + 2 * len(NAMES) + 1).column_letter}2')
put(ws, 33, c0, '점 = 20분 구간 1개. 점선 = 워크로드 전환, 위 글자 = 그 구간의 워크로드. ' + NOTE)

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

# ---- Fig.7 workbook: sheet 1 = (가) timeline, sheet 2 = (나) per-round curves; both charts also on sheet 1
wb = Workbook(); ws = wb.active; ws.title = '그림7 후보 줄이기'
cols = [('시간(h)', [round(h, 4) for h, _, _ in tr]), (f'남은 후보 수 (파티션 {PART}, 판단마다)', [a for _, _, a in tr]), ('학습 회차', [e for _, e, _ in tr])]
table(ws, 1, cols)
c0 = len(cols) + 2; lc, nl = helpers(ws, c0, 49, 0, [(f'재설정{i + 1}', r) for i, r in enumerate(resets)])
ch = scatter(f'(가) 10시간 동안 v6의 남은 후보 수 (점 1개 = 판단 1번, 보라 선 = 변화 감지 → 다시 학습)', '측정 시작 후 시간 (시간)', '남은 후보 수', 12, 34, 0, 10, 1, 0, 50)
add(ch, ws, 1, len(tr), '2A78D6', 19050, 'circle', 3)
decorate(ch, ws, c0, lc, nl, '7D3CFF')
anchor = ws.cell(row=1, column=lc + 2 * len(NAMES) + 1).column_letter
ws.add_chart(ch, f'{anchor}2')
ws2 = wb.create_sheet('회차별 학습 곡선')
put(ws2, 1, 1, '판단 횟수', True); ws2.column_dimensions['A'].width = 10
for j in range(MAXJ): put(ws2, 2 + j, 1, j + 1)
for k, r in enumerate(rounds):
    a = r[4][:MAXJ]; put(ws2, 1, 2 + k, rlabel(r), True); ws2.column_dimensions[ws2.cell(row=1, column=2 + k).column_letter].width = 22
    for j, v in enumerate(a): put(ws2, 2 + j, 2 + k, v)
ch2 = scatter('(나) 학습 회차별: 재설정 후 판단이 쌓일수록 남은 후보 수 (줄어들면 = 학습). 처음 45번은 45개를 한 번씩 시험', '재설정 후 판단 횟수', '남은 후보 수', 13, 34, 0, MAXJ, 25, 0, 50)
for k, (r, c) in enumerate(zip(rounds, RCOL)):
    a = r[4][:MAXJ]; strong = any(w.split('.')[1] in NARROW for w in r[3]) and min(a) <= 10
    s = Series(Reference(ws2, min_col=2 + k, min_row=1, max_row=len(a) + 1), Reference(ws2, min_col=1, min_row=2, max_row=len(a) + 1), title_from_data=True)
    s.smooth = False; s.graphicalProperties.line.solidFill = c[1:].upper(); s.graphicalProperties.line.width = 34925 if strong else 19050
    s.marker.symbol = 'circle'; s.marker.size = 4 if strong else 3
    s.marker.graphicalProperties.solidFill = c[1:].upper(); s.marker.graphicalProperties.line.solidFill = c[1:].upper()
    ch2.series.append(s)
ws2.add_chart(ch2, 'J2')
put(ws2, 30, 10, '굵은 빨강·파랑 = 6번 FIO-Fast, 7번 Varmail 회차(45→5). 회색 = 나머지 회차(후보끼리 차이가 작아 거의 안 줄어듦).')
from copy import deepcopy
ch2b = deepcopy(ch2); ch2b.anchor = f'{anchor}27'; ws.add_chart(ch2b)   # same chart also under (가) on sheet 1
put(ws, len(tr) + 4, 1, f'보라 = 변화 감지 → 처음부터 다시 학습 (파티션 {PART}, {len(resets)}번). ' + NOTE)
wb.save(FIG / 'data' / 'fig7_v6_mixT.xlsx')
print('totals', {l: round(D[l][2], 3) for l in D}, '| resets h', [round(r, 2) for r in resets])
for r in rounds: print(rlabel(r), 'min', min(r[4]))
