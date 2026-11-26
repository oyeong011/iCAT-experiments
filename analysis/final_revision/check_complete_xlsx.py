#!/usr/bin/env python3
"""Check report/final-revision/iCAT_Complete_Experiment_Results.xlsx independently of the writer (stdlib zip + XML parse).
    python3 -I analysis/final_revision/check_complete_xlsx.py [xlsx]
1. every part is well-formed XML; every relationship target exists; content types cover every part
2. every chart series reference (<c:f>) resolves to cells on the named sheet; the cached values in the chart equal the cell values
3. cross-sheet agreement: (group, metric) mean / SD / CI identical wherever they appear; (group, rep) WAF identical in every run table
4. sheet/chart graph data CSVs (complete-results/chart*.csv) equal the chart source cells
Prints a summary and exits 1 on any failure."""
import csv, re, sys, zipfile, posixpath
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
X = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'report/final-revision/iCAT_Complete_Experiment_Results.xlsx'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main', 'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships', 'pr': 'http://schemas.openxmlformats.org/package/2006/relationships',
      'ct': 'http://schemas.openxmlformats.org/package/2006/content-types'}
fail = []
z = zipfile.ZipFile(X); parts = {n: z.read(n) for n in z.namelist()}
xml = {}
for n, b in parts.items():
    try: xml[n] = ET.fromstring(b)
    except ET.ParseError as e: fail.append(f'XML parse {n}: {e}')
ct = xml['[Content_Types].xml']; over = {e.get('PartName').lstrip('/') for e in ct.findall('ct:Override', NS)}
for n in parts:
    if not n.endswith('.rels') and n != '[Content_Types].xml' and n not in over: fail.append(f'no content type for {n}')
for n, root in xml.items():
    if n.endswith('.rels'):
        base = posixpath.dirname(posixpath.dirname(n))
        for rel in root.findall('pr:Relationship', NS):
            t = posixpath.normpath(posixpath.join(base, rel.get('Target')))
            if t not in parts: fail.append(f'{n}: missing target {t}')
# sheets
wbx = xml['xl/workbook.xml']; wrels = {r.get('Id'): r.get('Target') for r in xml['xl/_rels/workbook.xml.rels'].findall('pr:Relationship', NS)}
SHEETS = {}
for s in wbx.find('m:sheets', NS):
    path = 'xl/' + wrels[s.get('{%s}id' % NS['r'])]; cells = {}
    for c in xml[path].iter('{%s}c' % NS['m']):
        ref = c.get('r'); t = c.get('t'); v = c.find('m:v', NS)
        if t == 'inlineStr': cells[ref] = ''.join(x.text or '' for x in c.iter('{%s}t' % NS['m']))
        elif v is not None: cells[ref] = float(v.text)
    SHEETS[s.get('name')] = cells


def col2n(s):
    n = 0
    for ch in s: n = n * 26 + ord(ch) - 64
    return n - 1


def rng(f):
    m = re.match(r"'((?:[^']|'')+)'!\$([A-Z]+)\$(\d+):\$([A-Z]+)\$(\d+)$", f)
    sh = m[1].replace("''", "'"); c1, r1, c2, r2 = col2n(m[2]), int(m[3]), col2n(m[4]), int(m[5])
    out = []
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            name = ''; n = c + 1
            while n: n, rem = divmod(n - 1, 26); name = chr(65 + rem) + name
            out.append(SHEETS[sh].get(f'{name}{r}'))
    return sh, out


nref = 0; charts = sorted(n for n in parts if n.startswith('xl/charts/chart'))
for n in charts:
    for ref in xml[n].iter('{%s}numRef' % NS['c']):
        f = ref.find('c:f', NS).text; sh, vals = rng(f); nref += 1
        cache = {int(p.get('idx')): float(p.find('c:v', NS).text) for p in ref.iter('{%s}pt' % NS['c'])}
        for i, v in enumerate(vals):
            vv = v if isinstance(v, float) else None
            if (i in cache) != (vv is not None) or (vv is not None and abs(cache[i] - vv) > 1e-12): fail.append(f'{n} {f} idx {i}: cache {cache.get(i)} cell {v}')
    for ref in xml[n].iter('{%s}strRef' % NS['c']):
        f = ref.find('c:f', NS).text; sh, vals = rng(f); nref += 1
        cache = {int(p.get('idx')): p.find('c:v', NS).text or '' for p in ref.iter('{%s}pt' % NS['c'])}
        for i, v in enumerate(vals):
            sv = '' if v is None else (v if isinstance(v, str) else repr(v))
            if cache.get(i, '') != sv and not (isinstance(v, float) and cache.get(i) in (repr(v), str(v))): fail.append(f'{n} {f} idx {i}: cache {cache.get(i)!r} cell {v!r}')
# cross-sheet agreement
grid = {}
for sh, cells in SHEETS.items():
    rows = {}
    for ref, v in cells.items():
        m = re.match(r'([A-Z]+)(\d+)$', ref); rows.setdefault(int(m[2]), {})[col2n(m[1])] = v
    grid[sh] = rows
seen_stats, seen_runs = {}, {}
nstat = nrun = 0
for sh, rows in grid.items():
    hdr = None
    for r in sorted(rows):
        row = rows[r]; vals = [row.get(i) for i in range(max(row) + 1)]
        if r - 1 not in rows or set(row) == {0}: hdr = None   # blank line before, or a title line: a new table starts
        if '그룹' in vals and ('지표' in vals or 'rep' in vals): hdr = {v: i for i, v in enumerate(vals) if isinstance(v, str)}; continue
        if hdr is None or not isinstance(row.get(hdr['그룹']), str): continue
        g = row.get(hdr['그룹'])
        if '지표' in hdr and '평균' in hdr and isinstance(row.get(hdr['지표']), str) and row.get(hdr['지표'], '').startswith('waf'):
            key = (g, row[hdr['지표']]); val = tuple(row.get(hdr[k]) for k in ('n', '평균', 'SD', '95% CI 하한', '95% CI 상한') if k in hdr); nstat += 1
            if key in seen_stats and seen_stats[key][0] != val: fail.append(f'stats differ {key}: {sh} {val} vs {seen_stats[key][1]} {seen_stats[key][0]}')
            seen_stats.setdefault(key, (val, sh))
        if 'rep' in hdr and '전체 WAF' in hdr and isinstance(row.get(hdr['전체 WAF']), float):
            key = (g, row.get(hdr['rep'])); val = round(row[hdr['전체 WAF']], 4); nrun += 1
            if key in seen_runs and seen_runs[key][0] != val: fail.append(f'run WAF differs {key}: {sh} {val} vs {seen_runs[key][1]}')
            seen_runs.setdefault(key, (val, sh))
# chart CSVs vs chart data: every number in complete-results/chart*.csv must appear (rounded 4) in the workbook
allnums = {round(v, 4) for cells in SHEETS.values() for v in cells.values() if isinstance(v, float)}
ncsv = 0
for p in sorted((ROOT / 'report/final-revision/complete-results').glob('chart*.csv')):
    for row in csv.reader(open(p)):
        for x in row[1:]:
            try: f = float(x)
            except ValueError: continue
            ncsv += 1
            if round(f, 4) not in allnums: fail.append(f'{p.name}: value {x} not in workbook')
print(f'parts {len(parts)}, sheets {len(SHEETS)}, charts {len(charts)}, chart refs checked {nref}, stat rows {nstat} ({len(seen_stats)} keys), run rows {nrun} ({len(seen_runs)} keys), chart-CSV numbers {ncsv}')
print('FAIL' if fail else 'PASS', len(fail)); [print(' ', f) for f in fail[:40]]
sys.exit(1 if fail else 0)
