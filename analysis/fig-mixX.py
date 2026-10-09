#!/usr/bin/env python3
"""mixX (기준 워크로드: FIO·Varmail·OLTP 30분 × 20구간, 표 3 준비, YCSB 없음): 정책별 WAF 추이 + 구간별 WAF + v6 학습.
정책 4개 모두 이 PC: iCAT-v6, CAT-47(최적), CAT-50(견고), CAT-37(기본).
-> figs/fig6_mixX.png, figs/fig7_mixX_v6.png, figs/data/fig6_mixX.xlsx, figs/data/fig7_mixX_v6.xlsx
원천: result/cycle-20261007/mixX-<policy>-rep1."""
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
from openpyxl.drawing.image import Image as XLImage
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
spec = importlib.util.spec_from_file_location('v4log', '/home/oy/iCAT/analysis/v4-log.py'); v4log = importlib.util.module_from_spec(spec); spec.loader.exec_module(v4log)
R = Path('/home/oy/iCAT/result/cycle-20261007'); FIG = Path('/home/oy/iCAT/figs')
POL = [('CAT-37 (기본)', 'fixed37', '#e3a33b', 1.6), ('CAT-50 (견고)', 'fixed50', '#9a9994', 1.6),
       ('CAT-47 (최적)', 'fixed47', '#2b2a28', 1.6), ('iCAT-v6 (제안)', 'onlinev6', '#2a78d6', 2.6)]
POL = [(lab, R / f'mixX-{p}-rep1', c, lw) for lab, p, c, lw in POL if (R / f'mixX-{p}-rep1' / 'summary.txt').exists()]
PART, STEP = '2', 20 / 60
SL = [f'S{i:02d}' for i in range(1, 21)]; NAMES = [{'F': 'FIO-Fast', 'V': 'Varmail', 'O': 'OLTP'}[w] for w in 'F V O F O V F V O F O V F V O F O V F V'.split()]
TYPE = {'OLTP': 'DB 서버 흉내', 'Varmail': '메일 서버 흉내', 'FIO-Fast': '합성 덮어쓰기(6 GiB)'}
BAND = {'YCSB-A': '#f6f1e7', 'YCSB-B': '#f3ece0', 'OLTP': '#eaf3ee', 'Varmail': '#eef2fb', 'FIO-Fast': '#f7ecec'}
INK, INK2, BLUE, PUR = '#1d1d1f', '#6e6e73', '#2a78d6', '#7d3cff'
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 10.5, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.spines.left': False, 'axes.edgecolor': '#d2d2d7', 'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': '#ededf0',
                     'axes.axisbelow': True, 'xtick.color': INK2, 'ytick.color': INK2, 'ytick.left': False, 'axes.labelcolor': INK2})

def run(d):
    raw = [tuple(map(int, m.groups())) for l in open(d / 'control-series.txt') if (m := re.match(r'(\d+) .*active=1 .*host_pages=(\d+) gc_pages=(\d+)', l))]
    t0 = raw[0][0]; s = [((t - t0) / 3600, h, g) for t, h, g in raw]; w, k = [], 0.0
    while k + STEP <= s[-1][0] + 1e-9:
        a = min(s, key=lambda p: abs(p[0] - k)); b = min(s, key=lambda p: abs(p[0] - k - STEP))
        if b[1] > a[1]: w.append((round(k + STEP / 2, 4), round(1 + (b[2] - a[2]) / (b[1] - a[1]), 4)))
        k += STEP
    starts = [(dt.datetime.fromisoformat((d / f'phase-{c}-start.time').read_text().strip()).timestamp() - t0) / 3600 for c in SL]
    sm = (d / 'summary.txt').read_text()
    return w, starts, float(re.search(r'^total .*WAF=([\d.]+)', sm, re.M)[1]), [float(re.search(rf'^phase{c}\(\S+\) .*WAF=([\d.]+)', sm, re.M)[1]) for c in SL], s[-1][0]
DATA = {lab: run(d) for lab, d, *_ in POL}
V4 = 'iCAT-v6 (제안)'; _, starts, V4T, V4P, X1 = DATA[V4]
bounds = starts + [X1]; mids = [(bounds[i] + bounds[i + 1]) / 2 for i in range(len(NAMES))]
NOTE = 'FIO·Varmail·OLTP 30분 × 20구간, 표 3 준비(6 GiB FIO 파일 유지), YCSB 없음. 정책마다 1회, 모두 이 PC.'

# v4 learner rounds
L = v4log.lines(str(R / 'mixX-onlinev6-rep1'))
ts = lambda l: float(re.match(r'\[\s*(\d+\.\d+)\]', l)[1])
t0 = next(ts(l) for l in L if 'Measurement: command=start' in l)
tr = [((ts(l) - t0) / 3600, int(m[1]), int(m[2])) for l in L if (m := re.search(rf'part={PART} epoch=(\d+) window=\d+ .*?active=(\d+)', l))]
best = {}
for l in L:
    if (m := re.search(rf'part={PART} epoch=(\d+) window=\d+ .*?best=(\d+) ', l)): best[int(m[1])] = int(m[2])
rounds = []
for ep in sorted({e for _, e, _ in tr}):
    v = [(h, a) for h, e, a in tr if e == ep]; h0, h1 = v[0][0], v[-1][0]
    rounds.append((ep, h0, h1, [f'{i + 1}.{n}' for i, n in enumerate(NAMES) if min(h1, bounds[i + 1]) - max(h0, bounds[i]) > 0.25], [a for _, a in v]))
RW = {i: f'{r[0]}\n{" ".join(w.split(".")[1][:1] for w in r[3])}\n{len(r[4])}' for i, r in enumerate(rounds)}   # 회차 / 워크로드 머리글자 / 시험 수 (회차가 많아 짧게)
CH = [(i + j / len(r[4]), v) for i, r in enumerate(rounds) for j, v in enumerate(r[4]) if j == 0 or v != r[4][j - 1]]
SEQ = []
for i, r in enumerate(rounds):
    n = len(r[4]); keep = set(range(0, n, max(1, n // 70))) | {n - 1}; pts = []
    for j, v in enumerate(r[4]):
        x = i + j / n
        if j and v != r[4][j - 1]: pts.append((x, r[4][j - 1]))
        if j in keep or (j and v != r[4][j - 1]): pts.append((x, v))
    SEQ.append(pts)

# ---- PNG
f6, a6 = plt.subplots(figsize=(16, 5.6))
for i, n in enumerate(NAMES):
    a6.axvspan(bounds[i], bounds[i + 1], color=BAND[n], lw=0, zorder=0)
    if i: a6.axvline(bounds[i], color='#5a5955', lw=1.1, ls=(0, (4, 3)), zorder=1)
    a6.text(mids[i], 1.02, f'{i + 1}\n{n[:3]}', transform=a6.get_xaxis_transform(), ha='center', va='bottom', fontsize=7.5, color=INK)
for lab, d, c, lw in POL:
    w, _, tot, *_ = DATA[lab]; gap = '' if lab == V4 else f'  (v6 {(V4T / tot - 1) * 100:+.1f}%)'
    a6.plot([h for h, _ in w], [v for _, v in w], color=c, lw=lw, marker='o', ms=4.5 if lab == V4 else 3.5, label=f'{lab}   10시간 전체 {tot:.3f}{gap}', zorder=3 if lab == V4 else 2)
a6.set_xlim(0, X1); a6.set_xticks(range(0, int(X1) + 1)); a6.set_xlabel('측정 시작 후 시간 (시간)'); a6.set_ylabel('구간 WAF (20분, 낮을수록 좋음)')
a6.legend(loc='upper center', bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False)
f6.subplots_adjust(top=0.78)
f6.suptitle('mixX (FIO·Varmail·OLTP 30분 × 20구간): 정책별 WAF 추이', x=0.06, ha='left', y=0.99, fontsize=13.5, weight='bold', color=INK)
f6.text(0.06, 0.935, '점 = 20분 구간, 점선 = 워크로드 전환. ' + NOTE, fontsize=8.8, color=INK2)
f6.savefig(FIG / 'fig6_mixX.png', dpi=200, bbox_inches='tight')

f7, a7 = plt.subplots(figsize=(18, 6.2))
for i, r in enumerate(rounds):
    a7.axvspan(i, i + 1, color=BAND[r[3][0].split('.')[1]] if r[3] else '#f4f4f6', lw=0, zorder=0)
    a7.text(i + 0.5, -0.04, RW[i], transform=a7.get_xaxis_transform(), ha='center', va='top', fontsize=7.5, color=INK, linespacing=1.3)
    if i: a7.axvline(i, color=PUR, lw=2, zorder=4)
a7.plot([x for p in SEQ for x, _ in p], [y for p in SEQ for _, y in p], color=BLUE, lw=2.2, zorder=3)
a7.scatter([x for x, _ in CH], [y for _, y in CH], s=26, color=BLUE, edgecolor='white', linewidth=0.8, zorder=5)
for i, r in enumerate(rounds):
    lo = min(r[4])
    if False and lo < r[4][0]: a7.text(i + 0.5, 22, f'{r[4][0]}개 → 최소 {lo}개\n(마지막 최고 후보 {best.get(r[0], "-")}번)', ha='center', fontsize=10, color=BLUE, weight='bold', bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#d2d2d7', lw=0.8), zorder=6)
a7.set_xlim(0, len(rounds)); a7.set_xticks([]); a7.set_ylim(0, 50); a7.set_yticks([0, 5, 15, 30, 45]); a7.set_ylabel(f'남은 후보 수 (파티션 {PART})'); a7.grid(False); a7.yaxis.grid(True)
f7.subplots_adjust(top=0.82, bottom=0.22)
f7.suptitle('mixX: iCAT-v6의 학습 — 전환 감지 → 45개 다시 시험 → 줄이기', x=0.06, ha='left', y=0.99, fontsize=13.5, weight='bold', color=INK)
f7.text(0.06, 0.92, '칸 하나 = 학습 1회차(폭 같게, 아래 = 회차 번호 / 워크로드 머리글자 F·V·O / 시험 횟수). 보라 선 = 초기화(v6는 45개 전부 되살림).\n점 = 회차 시작과 후보를 버린 순간. 시험 1번 = 후보 하나를 512 MiB(GC 128번 이상) 써 보고 점수 매기기.', fontsize=9, color=INK2)
f7.savefig(FIG / 'fig7_mixX_v6.png', dpi=200, bbox_inches='tight')

# ---- xlsx helpers
HDR = PatternFill('solid', fgColor='EEF2FB')
def put(ws, r, c, v, bold=False):
    x = ws.cell(row=r, column=c, value=v)
    if bold: x.font = Font(bold=True); x.fill = HDR; x.alignment = Alignment(wrap_text=True, vertical='center')
def scatter(title, xt, yt, xmin, xmax, unit, ymin, ymax, h=13, w=34):
    ch = ScatterChart(); ch.title = title; ch.style = 13; ch.scatterStyle = 'lineMarker'; ch.height, ch.width = h, w; ch.legend.position = 'b'
    ch.x_axis.title = xt; ch.y_axis.title = yt; ch.x_axis.delete = False; ch.y_axis.delete = False
    ch.x_axis.scaling.min, ch.x_axis.scaling.max, ch.x_axis.majorUnit = xmin, xmax, unit; ch.y_axis.scaling.min, ch.y_axis.scaling.max = ymin, ymax
    ch.x_axis.majorGridlines = None; return ch
def series(ws, xc, yc, n, color, width, marker, size=4, noline=False):
    s = Series(Reference(ws, min_col=yc, min_row=1, max_row=n + 1), Reference(ws, min_col=xc, min_row=2, max_row=n + 1), title_from_data=True)
    s.smooth = False; s.graphicalProperties.line.solidFill = color; s.graphicalProperties.line.width = width
    if noline: s.graphicalProperties.line.noFill = True
    s.marker.symbol = marker
    if marker != 'none': s.marker.size = size; s.marker.graphicalProperties.solidFill = color; s.marker.graphicalProperties.line.solidFill = 'FFFFFF' if noline else color
    return s
def deco(ch, ws, c0, xs, ytop, ybot, labels, color='8A8984', dash=True):
    """10-07: same construction as the earlier working Excel figures (fig7-mixT.py): one 2-point series per vertical line,
    named after the segment that starts there, shown in the legend. No data-label series, no hidden legend entries."""
    for i, x in enumerate(xs):
        c = c0 + 2 * i; name = '→ ' + labels[i + 1][1] if i + 1 < len(labels) else f'선{i + 1}'
        put(ws, 1, c, f'{name} x', True); put(ws, 1, c + 1, name, True)
        for r, y in ((2, ybot), (3, ytop)): put(ws, r, c, round(x, 3)); put(ws, r, c + 1, y)
        s = series(ws, c, c + 1, 2, color, 12700, 'none')
        if dash: s.graphicalProperties.line.dashStyle = 'dash'
        ch.series.append(s)
    return c0 + 2 * len(xs)

# ---- Fig.6 workbook
wb = Workbook(); ws = wb.active; ws.title = '그림6 WAF 추이'
col = 1
for lab, d, c, lw in POL:
    w = DATA[lab][0]; put(ws, 1, col, f'{lab} 시간(h)', True); put(ws, 1, col + 1, f'{lab} 10시간 {DATA[lab][2]:.3f}', True)
    for i, (h, v) in enumerate(w, 2): put(ws, i, col, h); put(ws, i, col + 1, v)
    col += 2
ymax = round(max(v for lab in DATA for _, v in DATA[lab][0]) + 0.8)
ch = scatter('mixX: 20분 구간 WAF 추이 (점 = 20분, 낮을수록 좋음)', '측정 시작 후 시간 (시간)', 'WAF', 0, 10, 1, 0.9, ymax)
for k, (lab, d, c, lw) in enumerate(POL):
    ch.series.append(series(ws, 2 * k + 1, 2 * k + 2, len(DATA[lab][0]), c[1:].upper(), 34925 if lab == V4 else 19050, 'circle', 6 if lab == V4 else 4))
end = deco(ch, ws, col + 1, bounds[1:len(NAMES)], ymax - 0.3, 0.9, [(mids[i], f'{i + 1}.{n}') for i, n in enumerate(NAMES)])
ws.add_chart(ch, f'{ws.cell(row=1, column=end + 1).column_letter}2')
put(ws, 30, end + 1, '점선 = 워크로드 전환, 위 글자 = 구간. ' + NOTE)
w2 = wb.create_sheet('구간별 WAF')
hdr = ['구간', '종류'] + [lab for lab, *_ in POL] + [f'v6 vs {lab.split()[0]} (%)' for lab, *_ in POL if lab != V4]
for j, h in enumerate(hdr, 1): put(w2, 1, j, h, True)
for i, n in enumerate(NAMES):
    row = [f'{i + 1}. {n}', TYPE[n]] + [round(DATA[lab][3][i], 3) for lab, *_ in POL] + [round((V4P[i] / DATA[lab][3][i] - 1) * 100, 1) for lab, *_ in POL if lab != V4]
    for j, v in enumerate(row, 1): put(w2, 2 + i, j, v)
row = ['10시간 전체', ''] + [round(DATA[lab][2], 3) for lab, *_ in POL] + [round((V4T / DATA[lab][2] - 1) * 100, 1) for lab, *_ in POL if lab != V4]
for j, v in enumerate(row, 1): put(w2, len(NAMES) + 2, j, v, True)
for j in range(1, len(hdr) + 1): w2.column_dimensions[w2.cell(row=1, column=j).column_letter].width = 15
bc = BarChart(); bc.type = 'col'; bc.grouping = 'clustered'; bc.title = '구간별 평균 WAF (낮을수록 좋음)'; bc.y_axis.title = 'WAF'; bc.height, bc.width = 11, 30
bc.add_data(Reference(w2, min_col=3, max_col=2 + len(POL), min_row=1, max_row=len(NAMES) + 2), titles_from_data=True); bc.set_categories(Reference(w2, min_col=1, min_row=2, max_row=len(NAMES) + 2))
for sr, (lab, d, c, lw) in zip(bc.series, POL): sr.graphicalProperties.solidFill = c[1:].upper(); sr.graphicalProperties.line.noFill = True
bc.legend.position = 'b'; bc.x_axis.delete = False; bc.y_axis.delete = False; w2.add_chart(bc, f'A{len(NAMES) + 5}')
put(w2, len(NAMES) + 4, 1, '음수(%) = v6의 WAF가 더 낮음(좋음). ' + NOTE)
wb.save(FIG / 'data' / 'fig6_mixX.xlsx')

# ---- Fig.7 workbook (v4 learning)
wb = Workbook(); w3 = wb.active; w3.title = '그림7 v6 학습'
xs = [round(x, 4) for p in SEQ for x, _ in p]; ys = [y for p in SEQ for _, y in p]
put(w3, 1, 1, '진행 위치 (회차 + 회차 안 비율)', True); put(w3, 1, 2, f'남은 후보 수 (파티션 {PART})', True)
for i, (x, y) in enumerate(zip(xs, ys), 2): put(w3, i, 1, x); put(w3, i, 2, y)
put(w3, 1, 3, '점 x', True); put(w3, 1, 4, '회차 시작·후보 버린 순간', True)
for i, (x, y) in enumerate(CH, 2): put(w3, i, 3, round(x, 4)); put(w3, i, 4, y)
ch3 = scatter('mixX: v6 학습 — 전환 감지(보라) → 다시 시험 → 줄이기 (칸 하나 = 학습 1회차)', '학습 회차 (아래 표: 회차별 구간·시간)', '남은 후보 수', 0, len(rounds), 1, 0, 50)
ch3.series.append(series(w3, 1, 2, len(xs), '2A78D6', 25400, 'none'))
ch3.series.append(series(w3, 3, 4, len(CH), '2A78D6', 0, 'circle', 6, noline=True))
end3 = deco(ch3, w3, 6, list(range(1, len(rounds))), 48, 0, [(i + 0.5, ' '.join(RW[i].split('\n')[:2])) for i in range(len(rounds))], '7D3CFF', dash=False)
w3.add_chart(ch3, f'{w3.cell(row=1, column=end3 + 1).column_letter}2')
r0 = 32
for j, h in enumerate(['회차', '걸친 구간', '시작(h)', '끝(h)', '시험 횟수', '처음 후보', '최소 후보', '마지막 최고 후보'], 1): put(w3, r0, end3 + j, h, True)
for i, r in enumerate(rounds):
    for j, v in enumerate([r[0], ', '.join(r[3]), round(r[1], 2), round(r[2], 2), len(r[4]), r[4][0], min(r[4]), best.get(r[0])], 1): put(w3, r0 + 1 + i, end3 + j, v)
w4 = wb.create_sheet('판단별 원자료')
for j, h in enumerate(['시간(h)', '학습 회차', f'남은 후보 수 (파티션 {PART})'], 1): put(w4, 1, j, h, True)
for i, (h, e, a) in enumerate(tr, 2): put(w4, i, 1, round(h, 4)); put(w4, i, 2, e); put(w4, i, 3, a)
wb.save(FIG / 'data' / 'fig7_mixX_v6.xlsx')
print({l: DATA[l][2] for l in DATA})
for r in rounds: print(r[0], r[3], len(r[4]), r[4][0], '->', min(r[4]), 'best', best.get(r[0]))
