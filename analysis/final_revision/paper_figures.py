#!/usr/bin/env python3
"""Paper figure / table data (CSV + one Excel databook) from the verified derived CSVs. GoCom 2026-11-25. New directory only; figs/ is untouched.
    python3 -I analysis/final_revision/paper_figures.py  -> report/paper-figures/{F*.csv, T*.csv, iCAT_revision_databook.xlsx, MANIFEST.csv}
Every row keeps host and batch; nothing is pooled across hosts or batches. n<3 rows carry no statistics."""
import csv, hashlib, sys
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(Path(__file__).parent))
from xlsx_min import write_xlsx
A = ROOT / 'result/final-revision-analysis'; O = ROOT / 'report/paper-figures'; O.mkdir(parents=True, exist_ok=True)
rd = lambda p: list(csv.DictReader(open(p)))
LABEL = {'revA-v4': 'iCAT-v4', 'revA-v1': 'V1 no drift detection', 'revA-v2': 'V2 no elimination/settle', 'revA-random': 'Random Selection',
         'revB-v4': 'iCAT-v4', 'revB-noelim': 'NoElim', 'revB-nosettle': 'NoSettle', 'revB-arm60': 'Arm60',
         'revC:revC-v4': 'iCAT-v4', 'revC:revC-elim10': 'elim 10 %', 'revC:revC-elim25': 'elim 25 %', 'revC:revB-arm60': 'Arm60', 'revC:online': 'original iCAT',
         'revD-v4': 'iCAT-v4', 'revD-nodrift': 'NoDrift', 'revD-fullreset': 'FullReset'}
out = {}
# F1 policy WAF by batch (total and per phase), mean / SD / 95 % t-CI
st = rd(A / 'm4/stats.csv')
out['F1_policy_waf_by_batch'] = [dict(host=r['host'], batch=r['batch'], group=r['group'], policy=LABEL.get(r['group'], r['group']), metric=r['metric'], n=r['n_valid'],
                                      values=r['values'], mean=r['mean'], sd=r['sd'], ci95_lo=r['ci_lo'], ci95_hi=r['ci_hi'],
                                      kind='measured (raw counters, GoCom recomputation)') for r in st if r['metric'] in ('waf', 'waf_A', 'waf_B', 'waf_C')]
# F2 per-run values (scatter / error bars)
out['F2_runs'] = [dict(host=r['host'], batch=r['batch'], group=r['group'], policy=LABEL.get(r['group'], r['group']), rep=r['rep'], valid=r['valid'], invalid_reasons=r['reasons'],
                       waf=r['waf'], waf_A=r['waf_A'], waf_B=r['waf_B'], waf_C=r['waf_C'], ycsb_ops=r['ycsb_ops'], module_sha256=r['module_sha'], raw_dir=r['dir'])
                  for r in rd(A / 'm4/runs.csv')]
# F3 same-batch contrasts vs that batch's V4 (the only ones used for verdicts)
out['F3_contrasts_same_batch'] = [dict(contrast=r['contrast'], metric=r['metric'], delta=r['diff'], welch95_lo=r['ci_lo'], welch95_hi=r['ci_hi'], welch_df=r['welch_df'],
                                       hedges_g_reference=r['hedges_g'],
                                       verdict=('n<3: no statistics' if r['ci_lo'] == '' else 'difference' if float(r['ci_lo']) > 0 or float(r['ci_hi']) < 0 else 'not distinguished'))
                                  for r in rd(A / 'm4/contrasts.csv') if r['kind'].startswith('direct') and r['contrast'].split(' - ')[1].endswith('v4')]
# F4 E6 / E7 secondary (revC) and Holm sensitivity
out['F4_revC_E2E6E7_secondary'] = rd(A / 'revC_secondary.csv')
out['T1_revC_contrasts_holm'] = rd(A / 'revC_contrasts.csv')
# F5 adaptation
out['F5_adaptation_summary'] = rd(A / 'adaptation_summary.csv')
# F6 resource
out['F6_learner_elapsed_ktime'] = [dict(r, note='kernel ktime elapsed, NOT CPU time') for r in rd(A / 'cpu_overhead.csv')]
out['F6_latency_stats'] = rd(A / 'm5_stats.csv')
out['F6_memory'] = rd(A / 'memory_overhead.csv')
# F7 SmartGC (SeungCom mixY, n=1 each)
out['F7_smartgc_waf'] = [dict(r, note='SeungCom mixY, n=1 per policy: no statistics') for r in rd(A / 'm1_waf.csv')]
out['F7_smartgc_latency_fio'] = rd(A / 'm1_latency_fio.csv')
out['F7_smartgc_varmail'] = rd(A / 'm1_latency_varmail.csv')
# T2 parameters
out['T2_parameters'] = rd(A / 'parameter_sensitivity.csv')
man = []
for name, rows in out.items():
    p = O / f'{name}.csv'
    with open(p, 'w', newline='') as f:
        w = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r))); w.writeheader(); w.writerows(rows)
    man.append(dict(file=f'report/paper-figures/{name}.csv', rows=len(rows), sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
src = ['m4/stats.csv', 'm4/runs.csv', 'm4/contrasts.csv', 'revC_secondary.csv', 'revC_contrasts.csv', 'adaptation_summary.csv', 'cpu_overhead.csv',
       'm5_stats.csv', 'memory_overhead.csv', 'm1_waf.csv', 'm1_latency_fio.csv', 'm1_latency_varmail.csv', 'parameter_sensitivity.csv']
for s in src:
    man.append(dict(file=f'result/final-revision-analysis/{s}', rows='source', sha256=hashlib.sha256((A / s).read_bytes()).hexdigest()))
with open(O / 'MANIFEST.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, ['file', 'rows', 'sha256']); w.writeheader(); w.writerows(man)
readme = [['iCAT revision databook (GoCom)', datetime.now().isoformat(timespec='seconds')],
          ['generator', 'analysis/final_revision/paper_figures.py'],
          ['rule', 'host and batch kept on every row; no pooling across hosts/batches; n<3 has no statistics; verdict = Welch 95 % CI excludes 0'],
          ['labels', 'measured = recomputed from raw counters / logs; learner time = kernel ktime elapsed (NOT CPU time); memory = calculated (sizeof)'],
          ['pending', 'revE (NoElim, drift 12.5 %), SeungCom abl-20261125 and greedy-20261125 are not yet included'], [], ['sheet', 'rows', 'sha256 of the CSV']]
readme += [[m['file'].split('/')[-1][:-4], m['rows'], m['sha256']] for m in man if m['rows'] != 'source']
sheets = [('README', readme)]
for name, rows in out.items():
    keys = list(dict.fromkeys(k for r in rows for k in r)); sheets.append((name, [keys] + [[r.get(k, '') for k in keys] for r in rows]))
write_xlsx(O / 'iCAT_revision_databook.xlsx', sheets)
for m in man: print(m['file'], m['rows'])
