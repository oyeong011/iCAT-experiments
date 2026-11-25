#!/usr/bin/env python3
"""revC-20261124 final E2 / E6 / E7 tables (GoCom 2026-11-25). Reads only derived CSVs made from the raw logs:
  result/revC-20261124-analysis/{runs,learner_runs}.csv   (revC_analyze.py, revC_learner.py)
  result/final-revision-analysis/{adaptation_metrics,cpu_overhead,latency_comparison}.csv (m6_adapt.py, m5_resource.py)
Pre-registered (revC preregistration section 4): mean +- SD, 95 % t-CI, Welch 95 % CI vs revC-v4, same-rep paired 95 % CI, verdict by CI only.
NOT pre-registered (added on request, reported as sensitivity): Hedges g, Welch p and Holm adjustment over 4 contrasts x 2 metrics (total, phase C).
    python3 -I analysis/final_revision/revC_final.py  -> result/final-revision-analysis/revC_{contrasts,secondary}.csv"""
import csv, math, statistics as st
from pathlib import Path
from scipy import stats
ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'result/revC-20261124-analysis'; F = ROOT / 'result/final-revision-analysis'
POL = [('revC-v4', 'revC-v4', 'control iCAT-v4 (elim 15 %, 45 arms)'), ('revC-elim10', 'revC-elim10', 'E6 elim 10 %'),
       ('revC-elim25', 'revC-elim25', 'E6 elim 25 %'), ('revB-arm60', 'revC-arm60', 'E7 60 arms'), ('online', 'revC-online', 'E2 original iCAT')]
runs = [r for r in csv.DictReader(open(A / 'runs.csv')) if r['valid'] == 'True']
lrn = {(r['policy'], r['rep']): r for r in csv.DictReader(open(A / 'learner_runs.csv')) if r['smoke'] == 'False'}
adp = {(r['group'], r['rep']): r for r in csv.DictReader(open(F / 'adaptation_metrics.csv'))}
cpu = {(r['group'], r['rep']): r for r in csv.DictReader(open(F / 'cpu_overhead.csv'))}
lat = {(r['group'], r['rep']): r for r in csv.DictReader(open(F / 'latency_comparison.csv'))}
tq = lambda df: float(stats.t.ppf(.975, df))


def vals(pol, key):
    return {int(r['rep']): float(r[key]) for r in runs if r['policy'] == pol}


def contrast(x, c):
    a, b = list(x.values()), list(c.values()); n1, n2 = len(a), len(b)
    v1, v2 = st.variance(a) / n1, st.variance(b) / n2; d = st.mean(a) - st.mean(b); se = math.sqrt(v1 + v2)
    df = (v1 + v2) ** 2 / (v1 ** 2 / (n1 - 1) + v2 ** 2 / (n2 - 1))
    sp = math.sqrt(((n1 - 1) * st.variance(a) + (n2 - 1) * st.variance(b)) / (n1 + n2 - 2)); g = d / sp * (1 - 3 / (4 * (n1 + n2) - 9))
    p = 2 * stats.t.sf(abs(d / se), df)
    pr = [x[k] - c[k] for k in sorted(x) if k in c]; ph = tq(len(pr) - 1) * st.stdev(pr) / math.sqrt(len(pr))
    return dict(delta=d, welch_lo=d - tq(df) * se, welch_hi=d + tq(df) * se, welch_df=df, welch_p=p, hedges_g=g,
                paired_n=len(pr), paired_lo=st.mean(pr) - ph, paired_hi=st.mean(pr) + ph)


rows = []
for key, metric in (('waf', 'total'), ('waf_C', 'phase C'), ('waf_A', 'phase A'), ('waf_B', 'phase B')):
    c = vals('revC-v4', key)
    for pol, grp, lab in POL[1:]:
        x = vals(pol, key); r = dict(contrast=f'{pol} - revC-v4', label=lab, metric=metric, n=len(x), n_ctrl=len(c),
                                     mean=st.mean(x.values()), sd=st.stdev(x.values()), ctrl_mean=st.mean(c.values()), ctrl_sd=st.stdev(c.values()), **contrast(x, c))
        r['verdict'] = 'difference' if r['welch_lo'] > 0 or r['welch_hi'] < 0 else 'not distinguished'
        r['rel_pct'] = 100 * r['delta'] / r['ctrl_mean']; rows.append(r)
fam = [r for r in rows if r['metric'] in ('total', 'phase C')]; m = len(fam); prev = 0
for i, r in enumerate(sorted(fam, key=lambda r: r['welch_p'])):
    prev = max(prev, min(1, (m - i) * r['welch_p'])); r['holm_p_sensitivity'] = prev
with open(F / 'revC_contrasts.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r))); w.writeheader(); w.writerows(rows)
# secondary (descriptive, mean +- SD over 3 reps; no inference)
SEC = [('eliminations', lambda p, g, k: lrn[(p, k)]['eliminations']), ('learner_ms_ktime', lambda p, g, k: cpu[(g, k)]['learner_elapsed_ms_ktime']),
       ('per_decision_us', lambda p, g, k: cpu[(g, k)]['per_decision_us']), ('windows', lambda p, g, k: lrn[(p, k)]['windows']),
       ('explore_host_share_all', lambda p, g, k: lrn[(p, k)]['explore_host_share']), ('first_settle_s', lambda p, g, k: adp[(g, k)]['first_settle_s_latest_part'])]
for ph in 'BC':
    for k in ('detect_s', 'resets', 'restored_arms', 'elim_drops', 'resettle_from_reset_s_max', 'reexplore_windows_sum', 'explore_host_share', 'recovery_s'):
        SEC.append((f'{ph}_{k}', (lambda kk: lambda p, g, r: adp[(g, r)][kk])(f'{ph}_{k}')))
SEC += [('C_hot_p99_us', lambda p, g, k: lat[(g, k)]['C_hot_p99_us']), ('B_ycsb_ops_per_s', lambda p, g, k: lat[(g, k)]['B_ycsb_ops_per_s'])]
sec = []
for pol, grp, lab in POL:
    for name, fn in SEC:
        raw = [fn(pol, grp, str(k)) for k in (1, 2, 3)]; num = []
        for v in raw:
            try: num.append(float(v))
            except (TypeError, ValueError): pass
        r = dict(policy=pol, label=lab, metric=name, values=' / '.join(str(v) for v in raw))
        if len(num) == 3: r.update(mean=st.mean(num), sd=st.stdev(num))
        else: r['mean'] = f'{len(num)} numeric of 3 (no statistics)'
        sec.append(r)
with open(F / 'revC_secondary.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, ['policy', 'label', 'metric', 'values', 'mean', 'sd']); w.writeheader(); w.writerows(sec)
for r in rows:
    print(f"{r['contrast']:24s} {r['metric']:8s} {r['mean']:.4f}±{r['sd']:.4f} d={r['delta']:+.4f} ({r['rel_pct']:+.2f}%) W[{r['welch_lo']:+.4f},{r['welch_hi']:+.4f}] "
          f"P[{r['paired_lo']:+.4f},{r['paired_hi']:+.4f}] g={r['hedges_g']:+.2f} p={r['welch_p']:.4f} holm={r.get('holm_p_sensitivity', '')} {r['verdict']}")
for r in sec:
    print(r['policy'], r['metric'], r['values'], f"{r['mean']:.3f}±{r['sd']:.3f}" if 'sd' in r else r['mean'])
