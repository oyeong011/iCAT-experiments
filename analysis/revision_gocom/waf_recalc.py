#!/usr/bin/env python3
"""Independent WAF recalculation from raw FTL counter snapshots (GoCom, 2026-11-23). Read-only.

For every run directory listed below:
  T1  total WAF from final-control.txt `part=` lines (sum over partitions)            -> compare with summary.txt `total`
  T2  per-phase WAF from phase-<X>-start.txt / phase-<X>-end.txt snapshot differences  -> compare with summary.txt phase lines
  T3  per-partition WAF (final-control)
  T4  SmartGC builds: nand_pages printed by the module vs host - absorbed + evicted + gc recomputed per partition
  T5  host_pages / gc_pages in report tables (compare.csv, final-20261123 tables) vs raw
Counters are MEASURED (module counters over the measurement window); every WAF here is COMPUTED from them.
Output: result/revision-gocom-20261123/waf_recalc_{runs,phases,partitions}.csv
"""
import csv, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]; R = ROOT / 'result'
OUT = R / 'revision-gocom-20261123'; OUT.mkdir(parents=True, exist_ok=True)
DIRS = sorted((R / 'revA-20261114/raw').glob('mixFYF-*-rep[0-9]')) + sorted((R / 'revB-20261122/raw').glob('mixFYF-*-rep[0-9]')) + \
       [R / p for p in ('gc-20261010/mixY-fixed47-rep1', 'gc-20261010/mixY-arm37-rep1', 'gc-20261010/mixY-arm50-rep1',
                        'gc-20261010/mixY-onlinev6-rep1', 'gc-20261010/mixY-sg-arm47-rep1', 'gc-20261010/mixY-smartgc-eq8-rep1',
                        'smartgc-20261119/resume/mixY-smartgc-rep1', 'smartgc-20261119/resume/mixY-onlinev4-rep1',
                        'v7-20261011/mixY/mixY-onlinev7-rep1', 'v7-20261011-icat2/mixY/mixY-onlinev7-rep1',
                        'gocom-sg-20261119/mixY-smartgc-rep1', 'gocom-sg-20261119/mixY-smartgcq-rep1',
                        'gocom-sg-20261119/mixY-sg-greedy-rep1', 'gocom-sg-20261119/mixY-sg-arm47-rep1')]
kv = lambda l: dict(re.findall(r'(\w+)=(-?\d+)', l))


def parts(txt):
    return {int(d['part']): d for d in (kv(l) for l in txt.splitlines() if l.startswith('part='))}


def sg(txt):
    return {int(d['part']): d for d in (kv(l) for l in txt.splitlines() if l.startswith('smartgc part='))}


runs, phs, prt = [], [], []
for d in DIRS:
    if not (d / 'summary.txt').exists(): continue
    s = (d / 'summary.txt').read_text()
    m = re.search(r'^total .*host_pages=(\d+) gc_pages=(\d+) WAF=([\d.]+)', s, re.M)
    sh, sgc, sw = int(m[1]), int(m[2]), float(m[3])
    fc = (d / 'final-control.txt').read_text(); P = parts(fc); G = sg(fc)
    h = sum(int(x['host_pages']) for x in P.values()); g = sum(int(x['gc_pages']) for x in P.values())
    nand_mod = sum(int(x['nand_pages']) for x in G.values()) if G else None
    nand_re = sum(int(P[i]['host_pages']) - int(x['absorbed']) + int(x['evicted']) + int(P[i]['gc_pages']) for i, x in G.items()) if G else None
    absorbed = sum(int(x['absorbed']) for x in G.values()) if G else 0
    evicted = sum(int(x['evicted']) for x in G.values()) if G else 0
    waf_raw = 1 + g / h
    runs.append(dict(run=str(d.relative_to(ROOT)), summary_host=sh, final_host=h, summary_gc=sgc, final_gc=g,
                     summary_WAF=sw, recomputed_WAF=round(waf_raw, 6), abs_diff=round(abs(waf_raw - sw), 7),
                     absorbed=absorbed, evicted=evicted, nand_module=nand_mod, nand_recomputed=nand_re,
                     nand_match=(nand_mod == nand_re) if G else '', WAF_nand=round((nand_mod if G else h + g) / h, 6),
                     counters_match=(sh == h and sgc == g)))
    for i, x in sorted(P.items()):
        hp, gp = int(x['host_pages']), int(x['gc_pages'])
        prt.append(dict(run=d.name, part=i, host_pages=hp, gc_pages=gp, WAF=round(1 + gp / hp, 6) if hp else '',
                        absorbed=G[i]['absorbed'] if G else '', evicted=G[i]['evicted'] if G else '',
                        nand_pages=G[i]['nand_pages'] if G else hp + gp))
    for m2 in re.finditer(r'^phase(\w+?)\((\S+)\) host_pages=(\d+) gc_pages=(\d+) WAF=([\d.]+)', s, re.M):
        ph = m2[1]; a, b = d / f'phase-{ph}-start.txt', d / f'phase-{ph}-end.txt'
        if not (a.exists() and b.exists()): continue
        A, B = parts(a.read_text()), parts(b.read_text())
        dh = sum(int(B[i]['host_pages']) - int(A[i]['host_pages']) for i in B)
        dg = sum(int(B[i]['gc_pages']) - int(A[i]['gc_pages']) for i in B)
        w = 1 + dg / dh if dh else None
        phs.append(dict(run=d.name, phase=ph, workload=m2[2], summary_host=int(m2[3]), snap_host=dh, summary_gc=int(m2[4]), snap_gc=dg,
                        summary_WAF=float(m2[5]), snap_WAF=round(w, 6) if w else '', abs_diff=round(abs(w - float(m2[5])), 7) if w else ''))

for name, rows in (('runs', runs), ('phases', phs), ('partitions', prt)):
    with open(OUT / f'waf_recalc_{name}.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

# T5: report tables vs raw
rep = []
by = {r['run']: r for r in runs}
for row in csv.DictReader(open(R / 'smartgc-20261119/report/compare.csv')):
    r = by.get(row['dir'])
    if r: rep.append(('smartgc-20261119/report/compare.csv', row['label'], 'host_pages', row['host_pages'], r['final_host'], int(row['host_pages']) == r['final_host']))
    if r: rep.append(('smartgc-20261119/report/compare.csv', row['label'], 'WAF_nand', row['WAF_nand'], r['WAF_nand'], abs(float(row['WAF_nand']) - r['WAF_nand']) < 1e-4))
for row in csv.DictReader(open(R / 'final-20261123/tables/mixY_compare.csv')):
    r = by.get(row['raw_dir'])
    if r: rep.append(('final-20261123/tables/mixY_compare.csv', row['policy'] + ' ' + row['host'][:4], 'WAF_nand', row['WAF_nand'], r['WAF_nand'], abs(float(row['WAF_nand']) - r['WAF_nand']) < 1e-4))
for row in csv.DictReader(open(R / 'final-20261123/tables/fyf_runs.csv')):
    r = by.get(row['raw_dir'])
    if r: rep.append(('final-20261123/tables/fyf_runs.csv', row['run'], 'WAF_total', row['WAF_total'], r['recomputed_WAF'], abs(float(row['WAF_total']) - r['recomputed_WAF']) < 1e-4))
with open(OUT / 'waf_recalc_report_tables.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['table', 'row', 'field', 'table_value', 'raw_recomputed', 'match']); w.writerows(rep)

print('runs', len(runs), 'counter mismatch', [r['run'] for r in runs if not r['counters_match']],
      'max |dWAF|', max(r['abs_diff'] for r in runs))
print('nand mismatch', [r['run'] for r in runs if r['nand_match'] is False])
print('phases', len(phs), 'max |dWAF|', max(p['abs_diff'] for p in phs if p['abs_diff'] != ''),
      'host mismatch', sum(1 for p in phs if p['summary_host'] != p['snap_host']), 'gc mismatch', sum(1 for p in phs if p['summary_gc'] != p['snap_gc']))
print('report rows', len(rep), 'mismatch', [x for x in rep if not x[5]])
for r in runs:
    if 'smartgc' in r['run'] or 'sg-' in r['run']: print(r['run'], r['recomputed_WAF'], r['WAF_nand'], r['absorbed'], r['evicted'], r['nand_match'])
