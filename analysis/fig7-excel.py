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
for wl, fwl in [('OLTP → Varmail', 'OLTP → Varmail'), ('FIO-Fast → Varmail (2회차)', 'FIO-Fast → Varmail')]:   # 2회차 = 변화 감지·재설정이 일어난 실행
    t = [r for r in T if r['워크로드'] == wl and r['파티션'] == '0' and r['구간 WAF']]
    resets = [float(r['경과(분)']) for r in T if r['워크로드'] == wl and r['파티션'] == '0' and '재설정' in r['사건']]
    fx = {pol: [(float(r['경과(분)']), float(r['30초 WAF'])) for r in F if r['워크로드'] == fwl and r['정책'] == pol and r['30초 WAF']] for pol in ('CAT-47 (최적)', 'CAT-37 (기본)', 'CAT-50 (견고)')}
    f = fx['CAT-47 (최적)']
    x = [float(r['경과(분)']) for r in t]
    best = step(x, [int(r['추정 최선 조합']) for r in t]); act = step(x, [int(r['남은 후보 수']) for r in t])
    stt, swept = [], False   # 0 = 전수 순회 (첫 후보 제거 전), 1 = 탐색, 2 = 정착 — same rule as fig7-plot.py
    for i, r in enumerate(t):
        if i and r['세대(재설정마다 +1)'] != t[i - 1]['세대(재설정마다 +1)']: swept = False
        elif i and int(r['남은 후보 수']) < int(t[i - 1]['남은 후보 수']): swept = True
        stt.append(2 if r['정착(1=예)'] == '1' else (1 if swept else 0))
    stp = step(x, stt)
    sw = next(float(r['경과(분)']) for r in t if r['구간'].startswith('B'))
    cols = [('v4 시간(분)', x), ('iCAT-v4 구간 WAF', [float(r['구간 WAF']) for r in t]),
            ('CAT-47 시간(분)', [a for a, _ in f]), ('CAT-47 (최적) 30초 WAF', [b for _, b in f]),
            ('v4 시간(분) ', x), ('시험·사용한 조합', [int(r['이번 구간에 쓴 조합']) for r in t]),
            ('계단 시간(분)', [a for a, _ in best]), ('추정 최선 조합', [b for _, b in best]),
            ('계단 시간(분) ', [a for a, _ in act]), ('남은 후보 수', [b for _, b in act]),
            ('구간', [r['구간'] for r in t]), ('정착(1=예)', [int(r['정착(1=예)']) for r in t]), ('사건', [r['사건'] for r in t]),
            ('계단 시간(분)  ', [a for a, _ in stp]), ('학습 상태 (0=전수 순회, 1=탐색, 2=정착)', [b for _, b in stp]),
            ('CAT-37 시간(분)', [a for a, _ in fx['CAT-37 (기본)']]), ('CAT-37 (기본) 30초 WAF', [b for _, b in fx['CAT-37 (기본)']]),
            ('CAT-50 시간(분)', [a for a, _ in fx['CAT-50 (견고)']]), ('CAT-50 (견고) 30초 WAF', [b for _, b in fx['CAT-50 (견고)']])]
    ws = wb.create_sheet(wl.replace(' → ', '→').replace(' (2회차)', ' 재설정'))
    for j, (h, v) in enumerate(cols, 1):
        ws.cell(row=1, column=j, value=h).font = Font(bold=True)
        for i, val in enumerate(v, 2): ws.cell(row=i, column=j, value=val)
        ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = 14
    ws.cell(row=1, column=21, value='전환 시점(분)').font = Font(bold=True); ws.cell(row=2, column=21, value=round(sw, 2))
    ws.cell(row=3, column=21, value='※ 각 열 쌍(시간, 값)이 그래프의 선 하나. 색·굵기·제목은 차트를 클릭해서 수정.')
    xm = round(max(x) + 0.5); n = lambda c: len(cols[c - 1][1])
    def vline(col, lo, hi):   # two-point series = vertical line at the switch, named with its time so it shows in the legend
        ws.cell(row=1, column=col, value='전환 시간'); ws.cell(row=1, column=col + 1, value=f'워크로드 전환 ({sw:.1f}분)')
        for i, yv in enumerate((lo, hi), 2): ws.cell(row=i, column=col, value=round(sw, 2)); ws.cell(row=i, column=col + 1, value=yv)
        return (col, col + 1, 2, 'E5484D', 19050, False)
    wafs = cols[1][1] + cols[15][1] + cols[17][1]
    chart(ws, f'(가) {fwl}: 판단 구간별 WAF (낮을수록 좋음)', 'WAF', [(16, 17, n(17), 'E3A33B', 22225, False), (18, 19, n(19), '8E8E93', 22225, False), (1, 2, n(2), '2A78D6', 15875, False), vline(23, round(min(wafs) - 0.05, 1), round(max(wafs) + 0.05, 1))],
          round(min(wafs) - 0.05, 1), round(max(wafs) + 0.05, 1), xm, 'AF2')
    chart(ws, '(나) 학습 상태 (0 = 전수 순회, 1 = 탐색, 2 = 정착)', '상태', [(14, 15, n(15), '2A78D6', 28575, False), vline(25, -0.2, 2.2)], -0.2, 2.2, xm, 'AF21')
    # 조합 번호(E~H열)는 그래프에서 뺐지만 데이터는 남겨 둠
    extra = []
    if resets:   # purple vertical line at the change-detector reset, named with its time
        ws.cell(row=1, column=29, value='재설정 시간'); ws.cell(row=1, column=30, value=f'변화 감지 → 재설정 ({resets[0]:.1f}분)')
        for i, yv in enumerate((0, 48), 2): ws.cell(row=i, column=29, value=round(resets[0], 2)); ws.cell(row=i, column=30, value=yv)
        extra = [(29, 30, 2, '7D3CFF', 22225, False)]
    chart(ws, '(다) 활성 후보 수', '남은 후보 수', [(9, 10, n(10), '2A78D6', 28575, False), vline(27, 0, 48)] + extra, 0, 48, xm, 'AF40')
    for r in range(2, len(t) + 2):
        if str(ws.cell(row=r, column=11).value).startswith('B'): ws.cell(row=r, column=11).fill = PatternFill('solid', fgColor='E8F0FB')
wb.save('/home/oy/iCAT/figs/data/fig7.xlsx'); print('ok')
