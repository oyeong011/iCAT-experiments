#!/usr/bin/env python3
"""arm47-20261127 analysis (pre-registered: result/arm47-20261127/preregistration.md).
    python3 -I -B analysis/revision/arm47_analysis.py GOCOM_DIR
GOCOM_DIR = git archive origin/report/data-validity-20261124 result/revA-20261114/raw/mixFYF-arm47-rep1 extracted there (고컴 n=1, not pooled).
Reuses batchG_analysis.row (WAF two paths, validity, latency, seeds, sha). Outputs result/arm47-20261127-analysis/."""
import csv, re, sys, statistics as st
from pathlib import Path
sys.argv, G = sys.argv[:1], Path(sys.argv[1])          # keep batchG_analysis from reading argv
sys.path.insert(0, str(Path(__file__).resolve().parent))
import batchG_analysis as B
R, GA, ROOT = B.R, B.GA, B.ROOT
OUT = ROOT / 'result/arm47-20261127-analysis'; OUT.mkdir(exist_ok=True); R.OUT = OUT
new = [B.row('승컴', d) for d in sorted((ROOT / 'result/arm47-20261127/raw').glob('mixFYF-arm47-rep[123]'))]
old = [B.row('고컴', d) for d in sorted((G / 'result/revA-20261114/raw').glob('mixFYF-arm47-rep1'))]
v4 = [r for r in csv.DictReader(open(ROOT / 'result/batchG-20261126-analysis/runs.csv')) if r['policy'] == 'bg-v4']
for r in new + old:
    kl = (ROOT / r['dir'] if r['host'] == '승컴' else G / 'result/revA-20261114/raw' / Path(r['dir']).name) / 'kernel.log'
    t = kl.read_text(errors='replace')
    r['fixed_arm47_init_lines'] = len(re.findall(r'Fixed CAT init .*arm=47 ', t)); r['other_arm_init'] = len(re.findall(r'Fixed CAT init .*arm=(?!47 )\d+', t))
    r['watgc_lines'] = t.count('WATGC_V2')
    r['waf_paths_agree_1e-6'] = r.get('waf_paths_agree_1e-6', r['waf_paths_agree'])
xc = []
for l in open(ROOT / 'result/arm47-20261127/queue.log'):
    if (m := re.match(r'\S+\tmixFYF-arm47-rep(\d)\tOK\twaf=(\S+) waf_A=(\S+) waf_B=(\S+) waf_C=(\S+)', l)):
        r = next(x for x in new if x['rep'] == int(m[1]))
        for i, k in enumerate(('total_waf', 'A_waf', 'B_waf', 'C_waf')):
            xc.append({'rep': m[1], 'metric': k, 'runtime_check': m[2 + i], 'recomputed': r[k], 'agree_1e-6': abs(float(m[2 + i]) - r[k]) < 1e-6})
summ = (G / 'result/revA-20261114/raw/mixFYF-arm47-rep1/summary.txt').read_text()
xc.append({'rep': '고컴 1', 'metric': 'total_waf vs summary.txt', 'runtime_check': re.search(r'^total .*WAF=([\d.]+)', summ, re.M)[1], 'recomputed': old[0]['total_waf'],
           'agree_1e-6': abs(float(re.search(r'^total .*WAF=([\d.]+)', summ, re.M)[1]) - old[0]['total_waf']) < 1e-6})
K = ['total_waf', 'A_waf', 'B_waf', 'C_waf', 'C_first5min_waf', 'ycsb_throughput', 'ycsb_success', 'C_clat_mean_us_jobmean', 'C_clat_p99_us_jobmean', 'C_clat_p99.9_us_jobmean']
stat, con = [], []
for k in K:
    a = [r[k] for r in new if r['valid']]; b = [float(r[k]) for r in v4]
    stat.append({'metric': k, 'arm47_승컴_rep1_2_3': ' / '.join(f'{x:.6f}' for x in a), **R.desc(a), '고컴_n1': old[0][k] if old else '',
                 'diff_승컴mean_minus_고컴n1': st.mean(a) - old[0][k] if old and old[0][k] != '' else '', 'bg-v4_mean': st.mean(b)})
    if st.variance(a) + st.variance(b) > 0:
        con.append({'contrast': 'arm47 (승컴 11-27) - bg-v4 (승컴 11-26/27, other batch)', 'metric': k, **GA.welch(b, a)})
for n, rows in (('runs.csv', new + old), ('statistics.csv', stat), ('contrasts.csv', con), ('crosscheck.csv', xc)): R.write(n, rows)
for r in new + old: print(r['host'], r['rep'], r['valid'], r['invalid_reason'], f"{r['total_waf']:.6f}", r['module_sha256'], r['fio_seeds_A'], r['fixed_arm47_init_lines'], r['other_arm_init'], r['watgc_lines'], r['waf_paths_agree_1e-6'])
for s in stat: print(s)
for c in con: print(c['metric'], {k: round(v, 5) for k, v in c.items() if isinstance(v, float)})
print('crosscheck', sum(x['agree_1e-6'] for x in xc), '/', len(xc))
