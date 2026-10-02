#!/usr/bin/env python3
"""그림 7을 엑셀에서 직접 고칠 수 있게: 워크로드마다 시트 1개 = 데이터 + 엑셀 차트 3개((가) WAF, (나) 조합, (다) 후보 수) -> figs/data/fig7.xlsx
원천: figs/data/fig7_v4_trace.csv (파티션 0), figs/data/fig14_30s.csv (CAT-47 비교선)"""
import csv
from openpyxl import Workbook
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.styles import Font, PatternFill
T = list(csv.DictReader(open('/home/oy/iCAT/figs/data/fig7_v4_trace.csv', encoding='utf-8-sig')))
F = list(csv.DictReader(open('/home/oy/iCAT/figs/data/fig14_30s.csv', encoding='utf-8-sig')))
wb = Workbook(); wb.remove(wb.active)
def chart(ws, title, ytitle, series, ymin, ymax, xmax, anchor):
    ch = ScatterChart(); ch.title = title; ch.style = 13; ch.scatterStyle = 'lineMarker'; ch.display_blanks = 'span'
    ch.x_axis.title = '측정 시작 후 시간 (분)'; ch.y_axis.title = ytitle; ch.height, ch.width = 9, 28; ch.legend.position = 'b'
    ch.x_axis.delete = False; ch.y_axis.delete = False; ch.x_axis.scaling.min = 0; ch.x_axis.scaling.max = xmax; ch.x_axis.majorUnit = 5
    ch.y_axis.scaling.min = ymin; ch.y_axis.scaling.max = ymax
    for xcol, ycol, n, color, width, marker in series:
        s = Series(Reference(ws, min_col=ycol, min_row=1, max_row=n + 1), Reference(ws, min_col=xcol, min_row=2, max_row=n + 1), title_from_data=True)
        s.smooth = False
        if marker:   # points only
            s.marker.symbol = 'circle'; s.marker.size = 3; s.marker.graphicalProperties.solidFill = color; s.marker.graphicalProperties.line.solidFill = color
            s.graphicalProperties.line.noFill = True
        else:
            s.marker.symbol = 'none'; s.graphicalProperties.line.solidFill = color; s.graphicalProperties.line.width = width
        ch.series.append(s)
    ws.add_chart(ch, anchor)
def step(xs, ys):   # (x, y) pairs drawn as a staircase: hold the previous value until the next x
    out = []
    for i, (x, y) in enumerate(zip(xs, ys)):
        if i: out.append((x, ys[i - 1]))
        out.append((x, y))
    return out
for wl in ['OLTP → Varmail', 'FIO-Fast → Varmail']:
    t = [r for r in T if r['워크로드'] == wl and r['파티션'] == '0' and r['구간 WAF']]
    f = [(float(r['경과(분)']), float(r['30초 WAF'])) for r in F if r['워크로드'] == wl and r['정책'] == 'CAT-47 (최적)' and r['30초 WAF']]
    x = [float(r['경과(분)']) for r in t]
    best = step(x, [int(r['추정 최선 조합']) for r in t]); act = step(x, [int(r['남은 후보 수']) for r in t])
    sw = next(float(r['경과(분)']) for r in t if r['구간'].startswith('뒤'))
    cols = [('v4 시간(분)', x), ('iCAT-v4 구간 WAF', [float(r['구간 WAF']) for r in t]),
            ('CAT-47 시간(분)', [a for a, _ in f]), ('CAT-47 (최적) 30초 WAF', [b for _, b in f]),
            ('v4 시간(분) ', x), ('시험·사용한 조합', [int(r['이번 구간에 쓴 조합']) for r in t]),
            ('계단 시간(분)', [a for a, _ in best]), ('추정 최선 조합', [b for _, b in best]),
            ('계단 시간(분) ', [a for a, _ in act]), ('남은 후보 수', [b for _, b in act]),
            ('구간', [r['구간'] for r in t]), ('정착(1=예)', [int(r['정착(1=예)']) for r in t]), ('사건', [r['사건'] for r in t])]
    ws = wb.create_sheet(wl.replace(' → ', '→'))
    for j, (h, v) in enumerate(cols, 1):
        ws.cell(row=1, column=j, value=h).font = Font(bold=True)
        for i, val in enumerate(v, 2): ws.cell(row=i, column=j, value=val)
        ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = 14
    ws.cell(row=1, column=15, value='전환 시점(분)').font = Font(bold=True); ws.cell(row=2, column=15, value=round(sw, 2))
    ws.cell(row=3, column=15, value='※ 각 열 쌍(시간, 값)이 그래프의 선 하나. 색·굵기·제목은 차트를 클릭해서 수정.')
    xm = round(max(x) + 0.5); n = lambda c: len(cols[c - 1][1])
    wafs = cols[1][1] + cols[3][1]
    chart(ws, f'(가) {wl}: 판단 구간별 WAF (낮을수록 좋음)', 'WAF', [(3, 4, n(4), '1D1D1F', 19050, False), (1, 2, n(2), '2A78D6', 12700, False)],
          round(min(wafs) - 0.05, 1), round(max(wafs) + 0.05, 1), xm, 'Q2')
    chart(ws, '(나) 적용한 파라미터 조합', '조합 번호', [(5, 6, n(6), 'B0B0B5', 0, True), (7, 8, n(8), '2A78D6', 28575, False)], 10, 62, xm, 'Q21')
    chart(ws, '(다) 활성 후보 수', '남은 후보 수', [(9, 10, n(10), '2A78D6', 28575, False)], 0, 48, xm, 'Q40')
    for r in range(2, len(t) + 2):
        if str(ws.cell(row=r, column=11).value).startswith('뒤'): ws.cell(row=r, column=11).fill = PatternFill('solid', fgColor='E8F0FB')
wb.save('/home/oy/iCAT/figs/data/fig7.xlsx'); print('ok')
