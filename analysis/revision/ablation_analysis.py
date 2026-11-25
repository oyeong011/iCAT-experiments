#!/usr/bin/env python3
"""abl-20261125 analysis (pre-registered in result/revision-additional-ablation/preregistration.md).
    python3 -I -B analysis/revision/ablation_analysis.py
Primary: NoDiscount - V4, OffBundle - V4 (same-batch abl-v4), total & phase C WAF, Welch + Hedges' g, Holm over these 4.
Secondary: same-seed paired diffs (df 2); abl-v4 - revD-v4 reproducibility. Reuses greedy_analysis helpers (run_row, welch)."""
import statistics as st
from scipy import stats
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import greedy_analysis as GA
R = GA.R

A = R.ROOT / 'result/revision-additional-ablation'
POL = ['abl-v4', 'abl-nodiscount', 'abl-off-elim-settle-drift-probe']
KEYS = ['total_waf', 'A_waf', 'B_waf', 'C_waf', 'switches', 'eval_explore', 'elim', 'best_change', 'resets', 'settled_events', 'learner_ms', 'ycsb_ops']

def paired(rows, a, b, k):
    pa = {r['rep']: r[k] for r in rows if r['policy'] == a}; pb = {r['rep']: r[k] for r in rows if r['policy'] == b}
    dd = [pb[i] - pa[i] for i in (1, 2, 3)]; m, s = st.mean(dd), st.stdev(dd); h = stats.t.ppf(.975, 2) * s / 3 ** .5
    return {'paired_diffs': ' / '.join(f'{x:+.4f}' for x in dd), 'paired_mean': m, 'paired_ci_lo': m - h, 'paired_ci_hi': m + h,
            'paired_p': 2 * stats.t.sf(abs(m / (s / 3 ** .5)), 2) if s else float('nan')}

def holm(ps):   # step-down adjusted p, monotone
    o = sorted(range(len(ps)), key=ps.__getitem__); adj, run = [0] * len(ps), 0
    for r, i in enumerate(o): run = max(run, min(1, (len(ps) - r) * ps[i])); adj[i] = run
    return adj

if __name__ == '__main__':
    R.OUT = A
    dirs = [d for p in POL for d in sorted((A / 'raw').glob(f'mixFYF-{p}-rep[123]'))]
    revd = sorted((R.ROOT / 'result/revD-20261124/raw').glob('mixFYF-revD-v4-rep[123]'))
    runs = [GA.run_row(d) for d in dirs + revd]
    bad = [r['dir'] for r in runs if not r['valid']]
    assert not bad, f'invalid runs: {bad}'
    lm = []
    for d in dirs:
        _, c = GA.learner(d, R.policy(d), R.rep(d)); lm += c
    R.write('runs.csv', runs); R.write('learner_metrics.csv', lm)
    v = lambda p, k: [r[k] for r in runs if r['policy'] == p]
    R.write('statistics.csv', [{'policy': p, 'metric': k, 'values': ' / '.join(f'{x:.4f}' for x in v(p, k)), **R.desc(v(p, k))}
                               for p in POL + ['revD-v4'] for k in KEYS])
    con = [{'role': 'primary', 'contrast': f'{p} - abl-v4', 'metric': k, **GA.welch(v('abl-v4', k), v(p, k)), **paired(runs, 'abl-v4', p, k)}
           for p in POL[1:] for k in ('total_waf', 'C_waf')]
    for c, h in zip(con, holm([c['p'] for c in con])): c['holm_p'] = h
    con += [{'role': 'reproducibility', 'contrast': 'abl-v4 - revD-v4', 'metric': k, **GA.welch(v('revD-v4', k), v('abl-v4', k)),
             **paired(runs, 'revD-v4', 'abl-v4', k)} for k in ('total_waf', 'C_waf')]
    R.write('contrasts.csv', con)
    for c in con: print(c['contrast'], c['metric'], *(f"{k}={c[k]:.4f}" for k in ('diff', 'ci_lo', 'ci_hi', 'p', 'hedges_g', 'paired_mean')), f"holm={c.get('holm_p', '')}")
