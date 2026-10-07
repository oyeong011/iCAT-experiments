#!/usr/bin/env python3
"""v6 불규칙 순서 혼합 10시간(mixT) 그림 2개 + 엑셀.
그림 6: 20분 구간 WAF 추이 - CAT-37(기본) / CAT-50(견고) / CAT-47(최적) / iCAT-v6, 구간별 평균 WAF 표.
그림 7: v6 학습 - 학습 회차를 같은 폭으로 시간 순서대로 이어 그림: 45개 -> 줄이기 -> 초기화(다시 45개) -> 다시 줄이기.
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

# Fig.7: every learning round gets the same width, drawn left to right in time order, so each reset is visible as
# "drop -> purple line -> back to 45 -> drop again". x inside a round = how far through that round's judgments.
def seq_points(maxpts=70):
    """step-shaped (x, y) per round: changes kept exactly, flat stretches thinned to ~maxpts markers"""
    out = []
    for i, (ep, h0, h1, wl, a) in enumerate(rounds):
        n = len(a); keep = set(range(0, n, max(1, n // maxpts))) | {n - 1}
        pts = []
        for j, v in enumerate(a):
            x = i + j / n
            if j and v != a[j - 1]: pts.append((x, a[j - 1]))   # step corner
            if j in keep or (j and v != a[j - 1]): pts.append((x, v))
        out.append(pts)
    return out
SEQ = seq_points()
RW = {i: f'{r[0]}회차\n{"+".join(w.split(".")[1] for w in r[3])}\n{r[1]:.1f}~{r[2]:.1f}h · 시험 {len(r[4])}번' for i, r in enumerate(rounds)}
f7, a7 = plt.subplots(figsize=(14, 6.4))
for i, r in enumerate(rounds):
    wl = r[3][0].split('.')[1]
    a7.axvspan(i, i + 1, color=BAND[wl], lw=0, zorder=0)
    a7.text(i + 0.5, -0.04, RW[i], transform=a7.get_xaxis_transform(), ha='center', va='top', fontsize=9, color=INK, linespacing=1.3)
    if i: a7.axvline(i, color=PUR, lw=2, zorder=4)
xs = [x for pts in SEQ for x, _ in pts]; ys = [y for pts in SEQ for _, y in pts]
xs2, ys2 = [], []
for k, pts in enumerate(SEQ):   # connect rounds: end of round k -> 45 at the start of round k+1 (the reset jump)
    xs2 += [x for x, _ in pts]; ys2 += [y for _, y in pts]
a7.plot(xs2, ys2, color=BLUE, lw=2.2, zorder=3)
CH = [(i + j / len(r[4]), v) for i, r in enumerate(rounds) for j, v in enumerate(r[4]) if j == 0 or v != r[4][j - 1]]   # round start + every removal
a7.scatter([x for x, _ in CH], [y for _, y in CH], s=26, color=BLUE, edgecolor='white', linewidth=0.8, zorder=5)
for i, r in enumerate(rounds):
    lo = min(r[4])
    if i: a7.annotate('초기화\n→ 45개로', (i, 45), (i + 0.03, 49.5), fontsize=8.5, color=PUR, weight='bold', va='top')
    if lo < r[4][0]:
        jl = r[4].index(lo); a7.annotate(f'{r[4][0]}→{lo}개', (i + jl / len(r[4]), lo), (6, -16 if lo > 10 else 8), textcoords='offset points', fontsize=10, color=BLUE, weight='bold')
    else:
        a7.text(i + 0.5, 41, '안 줄어듦\n(후보끼리 차이 작음)', ha='center', va='top', fontsize=8.5, color=INK2)
a7.set_xlim(0, len(rounds)); a7.set_xticks([]); a7.set_ylim(0, 50); a7.set_yticks([0, 5, 15, 30, 45]); a7.set_ylabel('남은 후보 수 (파티션 2)')
a7.grid(False); a7.yaxis.grid(True)
f7.subplots_adjust(top=0.74, bottom=0.2)
f7.suptitle('그림 7. iCAT-v6의 학습: 후보 45개 → 줄이기 → (워크로드 변화 감지) 초기화 → 다시 45개 → 다시 줄이기', x=0.06, ha='left', y=0.985, fontsize=13.5, weight='bold', color=INK)
f7.text(0.06, 0.89, '불규칙 순서 응용 혼합 10시간. 칸 하나 = 학습 1회차(폭은 같게 맞춤, 칸 안 왼쪽→오른쪽 = 시간 순서). 보라 선 = 초기화. 점 = 회차 시작과 후보를 버린 순간.\n'
         '시험 1번 = 후보 하나를 512 MiB 쓰는 동안(GC 128번 이상) 써 보고 WAF 점수를 매기는 것.\n'
         '각 회차는 먼저 45개를 한 번씩 다 시험하고(평평) 그다음 나쁜 후보를 버린다(하락). FIO-Fast·7번 Varmail에서 45→5.  ' + NOTE, fontsize=9, color=INK2)
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
    lines = lines or [(f'→ {i + 1}.{NAMES[i]}', bounds[i]) for i in range(1, len(NAMES))]   # 10-07: named lines in the legend
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
    # 10-07: no data-label series / hidden legend entries (Excel showed these charts broken); lines are named in the legend

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

# ---- Fig.7 workbook: same sequential-round chart; sheet 2 = raw per-judgment data
wb = Workbook(); ws = wb.active; ws.title = '그림7 v6 학습'
xs, ys = [round(x, 4) for pts in SEQ for x, _ in pts], [y for pts in SEQ for _, y in pts]
table(ws, 1, [('진행 위치 (회차 번호 + 회차 안 비율)', xs), ('남은 후보 수 (파티션 2)', ys)])
c0 = 4
for i in range(1, len(rounds)):   # purple reset lines
    c = c0 + 2 * (i - 1); put(ws, 1, c, f'초기화{i} x', True); put(ws, 1, c + 1, f'초기화 → {i + 1}회차', True)
    for r_, y in ((2, 0), (3, 48)): put(ws, r_, c, i); put(ws, r_, c + 1, y)
lc = c0 + 2 * (len(rounds) - 1)
for i, r in enumerate(rounds):    # round names written at the top of each slot
    put(ws, 1, lc + 2 * i, f'라벨{i + 1} x', True); put(ws, 1, lc + 2 * i + 1, RW[i].replace('\n', ' / '), True)
    put(ws, 2, lc + 2 * i, i + 0.5); put(ws, 2, lc + 2 * i + 1, 1)
ch = scatter('그림 7. v6 학습: 45개 → 줄이기 → 초기화(보라) → 다시 45개 → 다시 줄이기', '학습 회차 (칸 하나 = 1회차, 아래 글자 = 그 회차의 워크로드·시간)', '남은 후보 수', 14, 36, 0, len(rounds), 1, 0, 50)
add(ch, ws, 1, len(xs), '2A78D6', 25400, 'none')
put(ws, 1, 3, '점: 회차 시작·후보 버린 순간 x', True)
for k, (x, y) in enumerate(CH, 2): put(ws, k, 3, round(x, 4)); put(ws, k, c0 + 4 * len(rounds) + 2, y)
put(ws, 1, c0 + 4 * len(rounds) + 2, '회차 시작·후보 버린 순간', True)
s = Series(Reference(ws, min_col=c0 + 4 * len(rounds) + 2, min_row=1, max_row=len(CH) + 1), Reference(ws, min_col=3, min_row=2, max_row=len(CH) + 1), title_from_data=True)
s.marker.symbol = 'circle'; s.marker.size = 6; s.marker.graphicalProperties.solidFill = '2A78D6'; s.marker.graphicalProperties.line.solidFill = 'FFFFFF'; s.graphicalProperties.line.noFill = True
ch.series.append(s)
hidden = []
for i in range(1, len(rounds)):
    c = c0 + 2 * (i - 1)
    s = Series(Reference(ws, min_col=c + 1, min_row=1, max_row=3), Reference(ws, min_col=c, min_row=2, max_row=3), title_from_data=True)
    s.smooth = False; s.marker.symbol = 'none'; s.graphicalProperties.line.solidFill = '7D3CFF'; s.graphicalProperties.line.width = 22225
    hidden.append(len(ch.series)); ch.series.append(s)
ch.x_axis.majorGridlines = None
ws.add_chart(ch, f'{ws.cell(row=1, column=lc + 2 * len(rounds) + 1).column_letter}2')
put(ws, 32, lc + 2 * len(rounds) + 1, '보라 선 = 워크로드 변화 감지 → 초기화(다시 45개). 각 칸: 먼저 45개를 한 번씩 시험(평평) → 나쁜 후보 버림(하락). ' + NOTE)
ws2 = wb.create_sheet('판단별 원자료')
table(ws2, 1, [('시간(h)', [round(h, 4) for h, _, _ in tr]), ('학습 회차', [e for _, e, _ in tr]), ('남은 후보 수 (파티션 2)', [a for _, _, a in tr])])
wb.save(FIG / 'data' / 'fig7_v6_mixT.xlsx')
print('totals', {l: round(D[l][2], 3) for l in D}, '| resets h', [round(r, 2) for r in resets])
for r in rounds: print(rlabel(r), 'min', min(r[4]))
