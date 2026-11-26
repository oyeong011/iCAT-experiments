#!/usr/bin/env python3
"""Paper data v2 (GoCom, 11-26): the 11-25 databook (report/paper-figures/, verified, left untouched) + batches finished after it:
  E  = revE-20261125 (GoCom, NoElim / Drift12.5 %, n=3 each, same-batch V4)
  F  = abl-20261125 (SeungCom, NoDiscount / OffBundle, n=3 each, same-batch V4; GoCom independent recomputation 9/9 valid)
  D' = greedy-20261125 (SeungCom, online Greedy n=3; vs revD-v4 = indirect, different batch)
  M1 = m1-20261126 (GoCom, iCAT-v4 / SmartGC-EQ8, n=1 each) -- added only if result/m1-20261126-final/ exists.
    python3 -I analysis/final_revision/paper_figures_v2.py -> report/paper-figures-20261127/ (new directory; refuses to overwrite)
Rules: host and batch on every row, no pooling across hosts/batches, n<3 no statistics, cross-batch contrasts labelled indirect."""
import csv, hashlib, re, statistics as stt, sys
from datetime import datetime
from pathlib import Path
from scipy import stats as sps
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(Path(__file__).parent))
from xlsx_min import write_xlsx
OLD = ROOT / 'report/paper-figures'; O = ROOT / 'report/paper-figures-20261127'
if O.exists() and any(O.iterdir()): sys.exit(f'refusing to overwrite {O}')
O.mkdir(parents=True, exist_ok=True)
rd = lambda p: list(csv.DictReader(open(p)))
LAB = {'revE-v4': 'iCAT-v4', 'revE-noelim': 'NoElim (in-run elimination off)', 'revE-drift12': 'Drift threshold 12.5 %',
       'abl-v4': 'iCAT-v4', 'abl-nodiscount': 'NoDiscount', 'abl-offbundle': 'OffBundle (bundle off)', 'greedy': 'Online Greedy'}


def tci(v):
    n = len(v); m = stt.mean(v); s = stt.stdev(v); h = sps.t.ppf(.975, n - 1) * s / n ** .5
    return m, s, m - h, m + h


def welch(a, b):
    ma, mb, va, vb = stt.mean(a), stt.mean(b), stt.variance(a), stt.variance(b); na, nb = len(a), len(b)
    se = (va / na + vb / nb) ** .5; df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    h = sps.t.ppf(.975, df) * se; p = 2 * sps.t.sf(abs((ma - mb) / se), df)
    return ma - mb, ma - mb - h, ma - mb + h, df, p


out = {n: rd(OLD / f'{n}.csv') for n in ('F1_policy_waf_by_batch', 'F2_runs', 'F3_contrasts_same_batch', 'F4_revC_E2E6E7_secondary',
                                          'T1_revC_contrasts_holm', 'F5_adaptation_summary', 'F6_learner_elapsed_ktime', 'F6_latency_stats',
                                          'F6_memory', 'F7_smartgc_waf', 'F7_smartgc_latency_fio', 'F7_smartgc_varmail', 'T2_parameters')}
for r in out['F1_policy_waf_by_batch'] + out['F2_runs']: r.setdefault('source', 'databook 11-25')

# ---- E (revE, GoCom) ----
E = [r for r in rd(ROOT / 'result/revE-20261125-analysis/runs.csv')]
for r in E:
    out['F2_runs'].append(dict(host='고컴', batch='revE-20261125', group=r['policy'], policy=LAB[r['policy']], rep=r['rep'], valid=r['valid'], invalid_reasons=r['reasons'],
                               waf=r['waf'], waf_A=r['waf_A'], waf_B=r['waf_B'], waf_C=r['waf_C'], module_sha256='see raw environment.txt', raw_dir='result/revE-20261125/raw/' + Path(r['dir']).name,
                               source='result/revE-20261125-analysis/runs.csv'))
val = lambda rows, g, m: [float(r[m]) for r in rows if r['group' if 'group' in r else 'policy'] == g and r['valid'] == 'True']
for g in ('revE-v4', 'revE-noelim', 'revE-drift12'):
    for m in ('waf', 'waf_A', 'waf_B', 'waf_C'):
        v = val(E, g, m); mu, s, lo, hi = tci(v)
        out['F1_policy_waf_by_batch'].append(dict(host='고컴', batch='revE-20261125', group=g, policy=LAB[g], metric=m, n=len(v), values=' / '.join(f'{x:.4f}' for x in v),
                                                  mean=mu, sd=s, ci95_lo=lo, ci95_hi=hi, kind='measured (raw counters, GoCom)', source='revE runs.csv'))
holm_rows = []
for g in ('revE-noelim', 'revE-drift12'):
    for m in ('waf', 'waf_A', 'waf_B', 'waf_C'):
        d, lo, hi, df, p = welch(val(E, g, m), val(E, 'revE-v4', m))
        out['F3_contrasts_same_batch'].append(dict(contrast=f'{g} - revE-v4', metric=m, delta=d, welch95_lo=lo, welch95_hi=hi, welch_df=df,
                                                   verdict='difference' if lo > 0 or hi < 0 else 'not distinguished', p_unadjusted=p,
                                                   host_batch='고컴 revE-20261125 (direct, same batch)'))
        if m in ('waf', 'waf_C'): holm_rows.append([f'{g} - revE-v4', m, p])
# Holm over the 4 pre-specified E tests (2 contrasts x total/phase-3), same as revE_final.md
k = len(holm_rows); run = 0
for i, (c, m, p) in enumerate(sorted(holm_rows, key=lambda x: x[2])):
    run = max(run, min(1, (k - i) * p))
    for r in out['F3_contrasts_same_batch']:
        if r['contrast'] == c and r['metric'] == m: r['p_holm_4tests'] = run

# ---- F (abl, SeungCom) and D' (greedy, SeungCom), GoCom independent recomputation ----
for tag, d in (('abl', 'abl-20261125-verify'), ('greedy', 'greedy-20261125-verify')):
    base = ROOT / 'result' / d
    for r in rd(base / 'runs.csv'):
        if r['group'] not in LAB or tag not in r['batch']: continue   # reference rows (revD-v4, abl-v4 in the greedy dir) come from their own batch
        out['F2_runs'].append(dict(host=r['host'], batch=r['batch'], group=r['group'], policy=LAB[r['group']], rep=r['rep'], valid=r['valid'], invalid_reasons=r['reasons'],
                                   waf=r['waf'], waf_A=r['waf_A'], waf_B=r['waf_B'], waf_C=r['waf_C'], ycsb_ops=r.get('ycsb_ops', ''), module_sha256=r['module_sha'],
                                   raw_dir='SeungCom push: ' + re.sub(r'^.*/scratchpad/[^/]+/', '', r['dir']), source=f'result/{d}/runs.csv'))
    for r in rd(base / 'stats.csv'):
        if r['group'] in LAB and tag in r['batch'] and r['metric'] in ('waf', 'waf_A', 'waf_B', 'waf_C'):
            out['F1_policy_waf_by_batch'].append(dict(host=r['host'], batch=r['batch'], group=r['group'], policy=LAB[r['group']], metric=r['metric'], n=r['n_valid'],
                                                      values=r['values'], mean=r['mean'], sd=r['sd'], ci95_lo=r['ci_lo'], ci95_hi=r['ci_hi'],
                                                      kind='measured (SeungCom raw, GoCom independent recomputation)', source=f'result/{d}/stats.csv'))
    for r in rd(base / 'contrasts.csv'):
        lo, hi = float(r['ci_lo']), float(r['ci_hi'])
        out['F3_contrasts_same_batch'].append(dict(contrast=r['contrast'], metric=r['metric'], delta=r['diff'], welch95_lo=lo, welch95_hi=hi, welch_df=r['welch_df'],
                                                   hedges_g_reference=r['hedges_g'], host_batch=r['kind'],
                                                   verdict=('difference' if lo > 0 or hi < 0 else 'not distinguished') + ('' if r['kind'].startswith('direct') else ' (INDIRECT: different batch)')))

# ---- E adaptation (phase 3) ----
A = rd(ROOT / 'result/revE-20261125-analysis/adaptation_revE.csv')
for g in ('revE-v4', 'revE-noelim', 'revE-drift12'):
    rows = [r for r in A if r['group'] == g]
    for col in rows[0]:
        if col in ('group', 'host', 'batch', 'rep', 'valid', 'dir', 'learner_log'): continue
        try: v = [float(r[col]) for r in rows]
        except ValueError: continue
        out['F5_adaptation_summary'].append(dict(group=g, host='고컴', batch='revE-20261125', metric=col, n_valid=len(v), values=' / '.join(f'{x:g}' for x in v),
                                                 mean=round(stt.mean(v), 4), sd=round(stt.stdev(v), 4) if len(v) > 2 else ''))

# ---- M1 (n=1 each) if the final tables exist ----
M1 = ROOT / 'result/m1-20261126-final'
if (M1 / 'kernel_elapsed_time.csv').exists():
    for n in ('kernel_elapsed_time', 'memory_comparison', 'memory_measured', 'memory_theoretical', 'userspace_cpu_time', 'common_vs_algorithm_cost'):
        out['F8_m1_' + n] = rd(M1 / f'{n}.csv')

# ---- validity table across all batches ----
out['T3_validity_all_runs'] = [dict(host=r['host'], batch=r['batch'], policy=r['policy'], rep=r['rep'], valid=r['valid'], invalid_reasons=r.get('invalid_reasons', ''),
                                    raw_dir=r['raw_dir'], source=r.get('source', '')) for r in out['F2_runs']]

man = []
for name, rows in out.items():
    p = O / f'{name}.csv'
    with open(p, 'w', newline='') as f:
        w = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r))); w.writeheader(); w.writerows(rows)
    man.append(dict(file=f'report/paper-figures-20261127/{name}.csv', rows=len(rows), sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
with open(O / 'MANIFEST.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, ['file', 'rows', 'sha256']); w.writeheader(); w.writerows(man)
readme = [['iCAT revision databook v2 (GoCom)', datetime.now().isoformat(timespec='seconds')],
          ['generator', 'analysis/final_revision/paper_figures_v2.py (base: report/paper-figures/ of 11-25, unchanged)'],
          ['added', "revE-20261125 (E), abl-20261125 (F, SeungCom), greedy-20261125 (D', SeungCom)" + (', m1-20261126 (n=1 each)' if (M1 / 'kernel_elapsed_time.csv').exists() else '; m1-20261126 pending')],
          ['rule', 'host and batch on every row; no pooling across hosts/batches; n<3 no statistics; verdict = Welch 95 % CI excludes 0; INDIRECT = different batch'],
          ['labels', 'learner/GC time = kernel ktime elapsed (NOT CPU time); memory calculated = sizeof; measured = VmallocUsed delta'], [], ['sheet', 'rows', 'sha256']]
readme += [[m['file'].split('/')[-1][:-4], m['rows'], m['sha256']] for m in man]
sheets = [('README', readme)]
for name, rows in out.items():
    keys = list(dict.fromkeys(k for r in rows for k in r)); sheets.append((name[:31], [keys] + [[r.get(k, '') for k in keys] for r in rows]))
write_xlsx(O / 'iCAT_revision_databook_v2.xlsx', sheets)
for m in man: print(m['file'], m['rows'])
