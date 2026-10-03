#!/usr/bin/env python3
"""그림 6 (10시간판). OLTP -> Varmail 10시간: 10분 단위 구간 WAF, iCAT-v4 vs CAT-50(견고) vs CAT-37(기본)
-> figs/fig6_10h.(png|svg|pdf), figs/data/fig6_10h.xlsx (데이터 + 엑셀 차트, 직접 편집용)
원천: 각 실행의 control-series.txt (30초 누적 카운터). 10분 구간 WAF = 그 10분의 GC 쓰기 / 호스트 쓰기.
CAT-37은 두 번째 PC(icat-2) 실행. 아직 없는 실행은 건너뛴다."""
import re, datetime as dt
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from openpyxl import Workbook
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.styles import Font
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
R = Path('/home/oy/iCAT/result')
POL = [('iCAT-v4 (제안)', R / 'mix-20260911/mixO-onlinev4-rep1-x20', '#2a78d6', 2.4),
       ('CAT-50 (견고 설정)', R / 'mix-20260911/mixO-fixed50-rep1-x20', '#8e8e93', 1.8),
       ('CAT-37 (기본값)', R / 'mixO-fixed37-chunked-20261003/mixO-fixed37-rep1-x20', '#e3a33b', 1.8)]
STEP = 10 / 60
INK, INK2, RED = '#1d1d1f', '#6e6e73', '#e5484d'
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 10.5, 'axes.facecolor': 'white', 'figure.facecolor': 'white',
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False, 'axes.edgecolor': '#d2d2d7',
                     'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': '#ededf0', 'grid.linewidth': 0.8, 'axes.axisbelow': True,
                     'xtick.color': INK2, 'ytick.color': INK2, 'ytick.left': False, 'axes.labelcolor': INK2, 'svg.fonttype': 'path'})

def run(d):
    raw = [tuple(map(int, m.groups())) for l in open(d / 'control-series.txt') if (m := re.match(r'(\d+) .*active=1 .*host_pages=(\d+) gc_pages=(\d+)', l))]
    t0 = raw[0][0]; s = [((t - t0) / 3600, h, g) for t, h, g in raw]
    sw = (dt.datetime.fromisoformat((d / 'phase-B-start.time').read_text().strip()).timestamp() - t0) / 3600
    out, k = [], 0.0
    while k + STEP <= s[-1][0] + 1e-9:   # exact bin WAF from cumulative counters
        a = min(s, key=lambda p: abs(p[0] - k)); b = min(s, key=lambda p: abs(p[0] - k - STEP))
        if b[1] > a[1]: out.append((round(k + STEP / 2, 4), 1 + (b[2] - a[2]) / (b[1] - a[1])))
        k += STEP
    sm = (d / 'summary.txt').read_text()
    tot, pa, pb = (float(re.search(rf'^{p} .*WAF=([\d.]+)', sm, re.M)[1]) for p in ('total', r'phaseA\(\w+\)', r'phaseB\(\w+\)'))
    return out, sw, tot, pa, pb
pol = [(lab, d, c, lw) for lab, d, c, lw in POL if (d / 'summary.txt').exists()]
D = {lab: run(d) for lab, d, *_ in pol}
sw = D['iCAT-v4 (제안)'][1]; xmax = max(D[l][0][-1][0] for l in D) + STEP / 2

# ---- PNG
fig, ax = plt.subplots(figsize=(12, 5.6))
ax.axvspan(sw, xmax, color='#f3f7fd', zorder=0, lw=0); ax.set_xlim(0, xmax)
ax.axvline(sw, color=RED, lw=1.1, ls=(0, (3, 3))); ax.text(sw, 0.02, f' 전환 {sw:.2f}시간', transform=ax.get_xaxis_transform(), fontsize=10, color=RED, weight='bold')
best = min(D, key=lambda l: D[l][2])
for lab, d, c, lw in pol:
    w, _, tot, pa, pb = D[lab]
    ax.plot([h for h, _ in w], [v for _, v in w], color=c, lw=lw, marker='o', ms=3.5,
            label=f'{lab}   전체 {tot:.3f}  (OLTP {pa:.3f} / Varmail {pb:.3f})' + ('  ← 가장 낮음' if lab == best and len(pol) > 1 else ''), zorder=3 if 'v4' in lab else 2)
ax.text(sw / 2, 0.5, '앞 워크로드: OLTP (15분 × 20회)', transform=ax.get_xaxis_transform(), ha='center', fontsize=11, color=INK2, weight='bold')
ax.text((sw + xmax) / 2, 0.5, '뒤 워크로드: Varmail (5시간)', transform=ax.get_xaxis_transform(), ha='center', fontsize=11, color='#2a78d6', weight='bold')
ax.set_xlabel('측정 시작 후 시간 (시간)'); ax.set_ylabel('구간 WAF (10분 단위, 낮을수록 좋음)'); ax.set_xticks(range(0, 11))
ax.legend(loc='upper left', fontsize=9.5, frameon=False)
fig.suptitle('그림 6. OLTP → Varmail 10시간 실행의 구간 WAF', x=0.06, ha='left', y=0.99, fontsize=13.5, weight='bold', color=INK)
fig.text(0.06, 0.925, '각 점 = 10분 동안의 WAF. 범례 = 10시간 전체 WAF와 구간별 WAF. 정책마다 별도 실행(CAT-37은 두 번째 PC), 각 1회.', fontsize=9.5, color=INK2)
fig.tight_layout(rect=(0, 0, 1, 0.91))
for e in ('png', 'svg', 'pdf'): fig.savefig(f'/home/oy/iCAT/figs/fig6_10h.{e}', dpi=200, bbox_inches='tight')

# ---- xlsx
wb = Workbook(); ws = wb.active; ws.title = '그림6 10시간 (10분 단위)'
col = 1
for lab, d, c, lw in pol:
    w = D[lab][0]
    ws.cell(row=1, column=col, value=f'{lab} 시간(h)').font = Font(bold=True); ws.cell(row=1, column=col + 1, value=f'{lab} 10분 구간 WAF').font = Font(bold=True)
    for i, (h, v) in enumerate(w, 2): ws.cell(row=i, column=col, value=h); ws.cell(row=i, column=col + 1, value=round(v, 4))
    col += 2
ws.cell(row=1, column=col + 1, value='전환 시간').font = Font(bold=True); ws.cell(row=1, column=col + 2, value=f'워크로드 전환 ({sw:.2f}시간)').font = Font(bold=True)
wafs = [v for l in D for _, v in D[l][0]]; ylo, yhi = round(min(wafs) - 0.05, 1), round(max(wafs) + 0.05, 1)
for i, yv in enumerate((ylo, yhi), 2): ws.cell(row=i, column=col + 1, value=round(sw, 3)); ws.cell(row=i, column=col + 2, value=yv)
ws.cell(row=5, column=col + 1, value='정책').font = Font(bold=True)
for j, h in enumerate(('10시간 전체 WAF', 'OLTP 구간', 'Varmail 구간'), 2): ws.cell(row=5, column=col + j, value=h).font = Font(bold=True)
for i, (lab, *_) in enumerate(pol, 6):
    ws.cell(row=i, column=col + 1, value=lab)
    for j, v in enumerate(D[lab][2:], 2): ws.cell(row=i, column=col + j, value=round(v, 3))
ch = ScatterChart(); ch.title = 'OLTP → Varmail 10시간: 10분 구간 WAF (낮을수록 좋음)'; ch.style = 13; ch.scatterStyle = 'lineMarker'; ch.display_blanks = 'span'
ch.x_axis.title = '측정 시작 후 시간 (시간)'; ch.y_axis.title = 'WAF'; ch.height, ch.width = 13, 28; ch.legend.position = 'b'
ch.x_axis.delete = False; ch.y_axis.delete = False; ch.x_axis.scaling.min = 0; ch.x_axis.scaling.max = 10.5; ch.x_axis.majorUnit = 1
ch.y_axis.scaling.min = ylo; ch.y_axis.scaling.max = yhi; ch.y_axis.number_format = '0.00'
for k, (lab, d, c, lw) in enumerate(pol):
    n = len(D[lab][0]); s = Series(Reference(ws, min_col=2 * k + 2, min_row=1, max_row=n + 1), Reference(ws, min_col=2 * k + 1, min_row=2, max_row=n + 1), title_from_data=True)
    s.smooth = False; s.graphicalProperties.line.solidFill = c[1:].upper(); s.graphicalProperties.line.width = int(lw * 12700)
    s.marker.symbol = 'circle'; s.marker.size = 4; s.marker.graphicalProperties.solidFill = c[1:].upper(); s.marker.graphicalProperties.line.solidFill = c[1:].upper()
    ch.series.append(s)
vl = Series(Reference(ws, min_col=col + 2, min_row=1, max_row=3), Reference(ws, min_col=col + 1, min_row=2, max_row=3), title_from_data=True)
vl.marker.symbol = 'none'; vl.graphicalProperties.line.solidFill = 'E5484D'; vl.graphicalProperties.line.dashStyle = 'dash'; ch.series.append(vl)
ws.add_chart(ch, f'{ws.cell(row=1, column=col + 6).column_letter}2')
wb.save('/home/oy/iCAT/figs/data/fig6_10h.xlsx')
print('drawn:', {l: round(D[l][2], 3) for l in D})
