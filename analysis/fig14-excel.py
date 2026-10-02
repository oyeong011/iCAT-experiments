#!/usr/bin/env python3
"""fig14 30초 WAF를 엑셀용으로: 워크로드마다 '경과(분) | v4 | 47 | 50 | 37' 표 (CSV 4개) + 시트 4개에 꺾은선 차트가 들어간 xlsx
원천: figs/data/fig14_30s.csv. 정책마다 30초 기록 시각이 조금씩 달라 0.5분 단위로 반올림해 같은 행에 맞춤."""
import csv, collections
from pathlib import Path
from openpyxl import Workbook
from openpyxl.chart import ScatterChart, Reference, Series
D = Path('/home/oy/iCAT/figs/data')
r = list(csv.DictReader(open(D / 'fig14_30s.csv', encoding='utf-8-sig')))
POL = ['iCAT-v4', 'CAT-47 (최적)', 'CAT-50 (견고)', 'CAT-37 (기본)']; COL = ['2A78D6', '2B2A28', 'A3A29D', 'E3A33B']
wb = Workbook(); wb.remove(wb.active)
for wl in dict.fromkeys(x['워크로드'] for x in r):
    t = collections.defaultdict(dict); sw = {}
    for x in r:
        if x['워크로드'] != wl: continue
        k = round(float(x['경과(분)']) * 2) / 2
        t[k][x['정책']] = float(x['30초 WAF']) if x['30초 WAF'] else None
        if x['구간'].startswith('뒤') and x['정책'] not in sw: sw[x['정책']] = float(x['경과(분)'])
    rows = [[k] + [t[k].get(p) for p in POL] for k in sorted(t)]
    name = wl.replace(' → ', '-to-').replace(' ', '')
    with open(D / f'fig14_lines_{name}.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['경과(분)'] + POL); w.writerows([[a] + ['' if v is None else f'{v:.4f}' for v in b] for a, *b in rows])
    ws = wb.create_sheet(wl.replace(' → ', '→')[:31])
    ws.append(['경과(분)'] + POL); [ws.append(x) for x in rows]
    ws['G1'] = '워크로드 전환 시점(분)'; [ws.cell(row=i + 2, column=7, value=f'{p}: {sw.get(p, 0):.1f}') for i, p in enumerate(POL)]
    ch = ScatterChart(); ch.title = f'{wl}: 30초마다 잰 WAF (낮을수록 좋음)'; ch.style = 13
    ch.x_axis.title = '실험 시작 후 시간 (분)'; ch.y_axis.title = '30초 WAF'; ch.height, ch.width = 11, 24
    ch.x_axis.delete = False; ch.y_axis.delete = False
    xs = Reference(ws, min_col=1, min_row=2, max_row=len(rows) + 1)
    for j, c in enumerate(COL):
        s = Series(Reference(ws, min_col=j + 2, min_row=1, max_row=len(rows) + 1), xs, title_from_data=True)
        s.marker.symbol = 'none'; s.smooth = False; s.graphicalProperties.line.solidFill = c; s.graphicalProperties.line.width = 32000 if j == 0 else 15000
        ch.series.append(s)
    ws.add_chart(ch, 'I2')
wb.save(D / 'fig14_lines.xlsx'); print('ok')
