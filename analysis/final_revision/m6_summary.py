#!/usr/bin/env python3
"""M6 summary tables (GoCom 2026-11-25). Reads result/final-revision-analysis/adaptation_metrics.csv (m6_adapt.py) and
result/final-revision-analysis/m4/runs.csv (og_audit.py). Groups are never pooled across batches or hosts; statistics only for n=3 numeric.
    python3 -I analysis/final_revision/m6_summary.py -> result/final-revision-analysis/{adaptation_summary.csv, parameter_sensitivity.csv}"""
import csv, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; F = ROOT / 'result/final-revision-analysis'
ad = list(csv.DictReader(open(F / 'adaptation_metrics.csv')))
KEYS = ['first_settle_s_latest_part'] + [f'{p}_{k}' for p in 'BC' for k in ('detect_s', 'resets', 'restored_arms', 'elim_drops', 'resettle_from_reset_s_max',
                                                                          'reexplore_windows_sum', 'explore_host_share', 'recovery_s')]
out = []
for g in dict.fromkeys(r['group'] for r in ad):
    rs = [r for r in ad if r['group'] == g and r['valid'] == 'True']
    for k in KEYS:
        raw = [r.get(k, '') for r in rs]; num = []
        for v in raw:
            try: num.append(float(v))
            except ValueError: pass
        row = dict(group=g, host=rs[0]['host'], batch=rs[0]['batch'], metric=k, n_valid=len(rs), values=' / '.join(raw))
        if len(num) == 3: row.update(mean=round(st.mean(num), 4), sd=round(st.stdev(num), 4))
        else: row['mean'] = f'{len(num)} numeric of {len(rs)}: no statistics'
        out.append(row)
with open(F / 'adaptation_summary.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, ['group', 'host', 'batch', 'metric', 'n_valid', 'values', 'mean', 'sd']); w.writeheader(); w.writerows(out)
# parameter table: code value (revC-src/conv_ftl.h) and what was measured. Evidence strings point at the report section holding the numbers.
P = [('WATGC_V2_ELIM_Q16', '9830 (15 %)', 'conv_ftl.h:39 (#ifndef)', '10 / 15 / 25 %', 'measured: revC n=3 each, same batch',
      'total WAF not distinguished (+1.1 %, +2.4 %); eliminations 45 / 30 / 23; learner 2.9 / 3.9 / 5.8 ms', 'report/final-revision/revC_E2_E6_E7_final.md#3'),
     ('elimination on/off (VARIANT 3)', 'on', 'conv_ftl.c', 'on / off (settle, drift on)', 'running: revE (n=3 + V4 n=3, same batch); revB n=3 has only a cross-batch control',
      'pending', 'result/revE-20261125/preregistration.md'),
     ('elimination + settle off (VARIANT 2)', 'on', 'conv_ftl.c', 'on / off', 'measured: revA n=3', 'V2 - V4 +0.135 [+0.117, +0.154]', 'report/final-revision/M4_statistics_final.md#3'),
     ('WATGC_V2_DRIFT_Q16', '16384 (25 %)', 'conv_ftl.h:75 (#ifndef)', '12.5 / 25 %', 'running: revE drift12 n=3', 'pending', 'result/revE-20261125/preregistration.md'),
     ('drift detection on/off (VARIANT 1)', 'on', 'conv_ftl.c', 'on / off', 'measured: revA n=3 (GoCom), revD n=3 (SeungCom)',
      'not distinguished in both batches (+0.079, +0.068 total)', 'report/final-revision/M4_statistics_final.md#3'),
     ('reset scope (VARIANT 7 full reset)', 'partial (restore eliminated arms of the shifted partition)', 'conv_ftl.c', 'partial / full', 'measured: revD n=3 (SeungCom)',
      'full - partial +0.060 [+0.016, +0.103] (Holm 0.072)', 'result/revD-20261124-verify/verify.md'),
     ('candidate space ARM_LO', '15 (45 arms)', 'conv_ftl.h', '45 / 60 arms', 'measured: revC n=3 each', 'total not distinguished (+0.028); phase A +3.0 %', 'report/final-revision/revC_E2_E6_E7_final.md#4'),
     ('WATGC_V2_GAMMA_Q16', '65503 (gamma 0.9995)', 'conv_ftl.h:61', '-', 'NOT measured as a level; discount on/off is SeungCom abl NoDiscount (running)', 'pending (SeungCom)', 'origin/main result/abl-20261125'),
     ('WATGC_V2_WINDOW_HOST_PAGES / WINDOW_GC', '131072 (512 MiB) / 128', 'conv_ftl.h:49-53 (#ifndef)', '256 MiB / 1 GiB (plan)', 'NOT measured; plan submitted, not approved',
      'unverified (empirical setting)', 'result/revE-20261125/window_plan.md'),
     ('UCB_C', '16384 (c = 0.25)', 'conv_ftl.h:63', '-', 'NOT measured', 'unverified', ''),
     ('STABLE / BEST_CONFIRMATIONS / TOLERANCE', '12 / 3 / 0.5 %', 'conv_ftl.h:66-69', 'settle on/off', 'settle off measured only bundled (V2 revA) or cross-batch (revB NoSettle)',
      'level sensitivity unverified', ''),
     ('PROBE_EVERY / STALE / DRIFT_WINDOWS / MIN_VISITS', '8 / 240 / 3 / 1', 'conv_ftl.h:64-77', '-', 'NOT measured', 'unverified', '')]
with open(F / 'parameter_sensitivity.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['parameter', 'code_value', 'location (revC-src)', 'levels', 'status', 'result', 'evidence']); w.writerows(P)
for r in out:
    if r['metric'] in ('first_settle_s_latest_part', 'C_detect_s', 'C_restored_arms', 'C_resettle_from_reset_s_max', 'C_reexplore_windows_sum', 'C_recovery_s', 'C_explore_host_share'):
        print(r['group'], r['metric'], r['values'], r['mean'], r.get('sd', ''))
