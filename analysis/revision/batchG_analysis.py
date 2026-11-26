#!/usr/bin/env python3
"""batchG-20261126 analysis (pre-registered: result/drift50-20261126/preregistration.md, result/greedygc-20261126/preregistration.md).
    python3 -I -B analysis/revision/batchG_analysis.py [GOCOM_DIR]
GOCOM_DIR (optional) = git archive origin/report/data-validity-20261124 result/revE-20261125 extracted there
  (고컴 revE drift12 / v4: separate host, reported side by side as within-host deltas, never pooled).
M3: greedygc - bg-v4 ; M6: drift50 - bg-v4 (+ 고컴 drift12 - revE-v4 reference). Same-batch bg-v4 is the only control.
Info only: bg-v4 vs revD-v4 / abl-v4 (batch reproducibility; not pooled).
Outputs result/batchG-20261126-analysis/{runs,adaptation_partition,reset_events,statistics,contrasts}.csv"""
import re, sys, statistics as st
from pathlib import Path
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
import greedy_analysis as GA
import secondary_metrics as SM
from ablation_analysis import paired, holm
R = GA.R; ROOT = R.ROOT
import os; OUT = Path(os.environ.get('BG_OUT', ROOT / 'result/batchG-20261126-analysis'))   # BG_OUT only for dry runs
SRC = {'bg-v4': 'result/batchG-20261126/raw', 'drift50': 'result/drift50-20261126/raw', 'greedygc': 'result/greedygc-20261126/raw',
       'revD-v4': 'result/revD-20261124/raw', 'abl-v4': 'result/revision-additional-ablation/raw'}
GOCOM = Path(sys.argv[1]) / 'result/revE-20261125/raw' if len(sys.argv) > 1 else None
R.SEUNG = Path('/')   # make GA.run_row always use R.rel below
R.rel = lambda d: str(d.relative_to(ROOT)) if ROOT in d.parents else f'origin/report/data-validity-20261124:{d.relative_to(d.parents[3])}'
LEARN = {'bg-v4', 'drift50', 'revD-v4', 'abl-v4', 'revE-v4', 'revE-drift12'}

def resets(d):
    """per reset: phase, part, deviation, active before (last sample of part before reset) / right after / max until next settle."""
    kl = (d / 'kernel.log').read_text(errors='replace').splitlines()
    start, samp, ev = R.klog(d); rows = []
    act = [(float(m[1]), int(m[2]), int(m[3])) for l in kl if (m := re.match(r'\[\s*([\d.]+)\] NVMeVirt: WATGC_V2 sample .*part=(\d) .*active=(\d+)', l))]
    for l in kl:
        if not (m := re.match(r'\[\s*([\d.]+)\] NVMeVirt: WATGC_V2 reset .*part=(\d) .*reason=(\S+) reference_q16=(\d+) sample_q16=(\d+)', l)): continue
        t, p, rf, sm = float(m[1]), int(m[2]), int(m[4]), int(m[5])
        s1 = min((x for x, k, q in ev if k == 'settled' and q == p and x > t), default=None)
        bef = [a for x, q, a in act if q == p and x < t]; aft = [a for x, q, a in act if q == p and x >= t and (s1 is None or x <= s1)]
        rows.append({'phase': R.phase_of(start, t), 'part': p, 't_from_phase_start_s': t - start[R.phase_of(start, t)], 'reason': m[3],
                     'deviation': abs(sm - rf) / rf, 'active_before': bef[-1] if bef else '', 'active_after': aft[0] if aft else '',
                     'active_max_until_settle': max(aft) if aft else '', 'resettle_s': s1 - t if s1 else ''})
    return rows

def row(host, d):
    r = GA.run_row(d, host); r['dir'] = R.rel(d)
    w = {x['dir']: x for x in R.waf_recalc([('승컴', d)])} if host == '승컴' else {}
    if w: r['waf_paths_agree_1e-6'] = w[r['dir']]['paths_agree_1e-6']; r['started_zero'] = w[r['dir']]['started_zero']
    for p in 'ABC':
        (sh, sg), _ = R.counters(d / f'phase-{p}-start.txt'); (eh, eg), _ = R.counters(d / f'phase-{p}-end.txt'); r[f'{p}_gc'] = eg - sg
    (th, tg), _ = R.counters(d / 'stopped.txt'); r['host_pages'], r['gc_pages'] = th, tg
    lat = R.latency([(host, d)])[0]
    r.update({k: v for k, v in lat.items() if k.startswith(('ycsb_', 'A_', 'C_')) and k not in r})
    r['fio_errors'] = sum(v for k, v in lat.items() if k.endswith('_err'))
    for ph in 'AC':   # mean over jobs of write clat
        for q in ('mean', 'p99', 'p99.9'):
            v = [x for k, x in lat.items() if k.startswith(f'{ph}_') and k.endswith(f'_clat_{q}_us')]
            r[f'{ph}_clat_{q}_us_jobmean'] = st.mean(v) if v else ''
    env = (d / 'environment.txt').read_text(errors='replace')
    r['module_sha256'] = (re.search(r'\b([0-9a-f]{64})\b', env) or [''])[0][:16]
    m = re.search(r'icat_seed=(\d+)', (d / 'kernel.log').read_text(errors='replace')); r['icat_seed'] = m[1] if m else 'none (no param)'
    import json; r['fio_seeds_A'] = '/'.join(j['job options'].get('randseed', '') for j in json.load(open(d / 'phase-A.json'))['jobs'])
    s, samp, ev = SM.klog_indep(d)
    pts = [x for x in R.ns['series'](d)]; t0 = dict((p, a) for p, a, b in R.ns['phases'](d))['C']
    pc = [x for x in pts if x[0] >= t0]; j = next((i for i, x in enumerate(pc) if x[0] >= t0 + 300), None)
    r['C_first5min_waf'] = 1 + (pc[j][2] - pc[0][2]) / (pc[j][1] - pc[0][1]) if j else ''
    if r['policy'] in LEARN:
        r.update({f'run_{k}': v for k, v in SM.explore_cost(samp).items()})
        r.update({f'C_{k}': v for k, v in SM.explore_cost(samp, s['C']).items()})
        rs = resets(d)
        for ph in 'ABC':
            x = [e for e in rs if e['phase'] == ph]
            r[f'{ph}_resets'] = len(x)
            r[f'{ph}_first_reset_s'] = min((e['t_from_phase_start_s'] for e in x), default='')
            r[f'{ph}_restored_active_mean'] = st.mean(e['active_after'] for e in x if e['active_after'] != '') if any(e['active_after'] != '' for e in x) else ''
            rt = [e['resettle_s'] for e in x if e['resettle_s'] != '']
            r[f'{ph}_resettle_s_mean'] = st.mean(rt) if rt else ''; r[f'{ph}_resettle_s_max'] = max(rt) if rt else ''
            r[f'{ph}_unresettled'] = sum(e['resettle_s'] == '' for e in x)
        r['resets_below_50pct'] = sum(e['deviation'] <= .5 for e in rs)
        e3 = R.e3([(host, d)])[1][0]
        for p in 'BC': r[f'{p}_recovery_s'] = e3.get(f'{p}_recovery_s', '')
        r['_resets'] = rs
    return r

def welch_or(a, b):
    return GA.welch(a, b) if len(a) == len(b) == 3 and st.variance(a) + st.variance(b) > 0 else {'diff': st.mean(b) - st.mean(a) if a and b else '', 'note': 'n<3 or zero variance: no test'}

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True); R.OUT = OUT
    runs = [row('승컴', d) for p, s in SRC.items() for d in sorted((ROOT / s).glob(f'mixFYF-{p}-rep[123]')) if (d / 'exit-code.txt').exists()]
    if GOCOM: runs += [row('고컴', d) for p in ('revE-v4', 'revE-drift12') for d in sorted(GOCOM.glob(f'mixFYF-{p}-rep[123]')) if (d / 'exit-code.txt').exists()]
    rev = [{'host': r['host'], 'policy': r['policy'], 'rep': r['rep'], **e} for r in runs for e in r.pop('_resets', [])]
    bad = [(r['dir'], r['invalid_reason']) for r in runs if not r['valid']]
    print('invalid:', bad or 'none')
    WK = ['total_waf', 'A_waf', 'B_waf', 'C_waf', 'C_first5min_waf']
    M6K = ['resets', 'A_resets', 'B_resets', 'C_resets', 'B_first_reset_s', 'C_first_reset_s', 'B_restored_active_mean', 'C_restored_active_mean',
           'B_resettle_s_mean', 'C_resettle_s_mean', 'C_resettle_s_max', 'C_unresettled', 'run_explore_host_share', 'run_explore_waf',
           'C_explore_host_share', 'B_recovery_s', 'C_recovery_s', 'learner_ms', 'resets_below_50pct']
    M3K = ['ycsb_throughput', 'ycsb_success', 'ycsb_READ_avg_us', 'ycsb_READ_p99_us', 'ycsb_UPDATE_avg_us', 'ycsb_UPDATE_p99_us',
           'A_clat_mean_us_jobmean', 'A_clat_p99_us_jobmean', 'A_clat_p99.9_us_jobmean', 'C_clat_mean_us_jobmean', 'C_clat_p99_us_jobmean',
           'C_clat_p99.9_us_jobmean', 'learner_ms', 'fio_errors', 'sqlite_full']
    v = lambda h, p, k: [r[k] for r in runs if r['host'] == h and r['policy'] == p and r['valid'] and r.get(k) not in ('', None)]
    pols = [('승컴', p) for p in SRC] + ([('고컴', p) for p in ('revE-v4', 'revE-drift12')] if GOCOM else [])
    stat = [{'host': h, 'policy': p, 'metric': k, 'values_rep1_2_3': ' / '.join(f'{x:.4f}' for x in v(h, p, k)), **R.desc(v(h, p, k))}
            for h, p in pols for k in dict.fromkeys(WK + M6K + M3K) if v(h, p, k)]
    con = []
    def add(role, h, a, b, keys):
        for k in keys:
            va, vb = v(h, a, k), v(h, b, k)
            if not va or not vb: continue
            c = {'question': role, 'host': h, 'contrast': f'{b} - {a}', 'metric': k, **welch_or(va, vb)}
            if len(va) == len(vb) == 3 and 'note' not in c and h == '승컴' and a == 'bg-v4':
                c.update(paired([r for r in runs if r['host'] == h], a, b, k))
            con.append(c)
    add('M3', '승컴', 'bg-v4', 'greedygc', WK + M3K)
    add('M6', '승컴', 'bg-v4', 'drift50', WK + M6K)
    if GOCOM: add('M6 (고컴 reference, not pooled)', '고컴', 'revE-v4', 'revE-drift12', WK + M6K)
    for ref in ('revD-v4', 'abl-v4'): add('batch reproducibility (info)', '승컴', ref, 'bg-v4', ['total_waf', 'C_waf'])
    prim = [c for c in con if c['question'] in ('M3', 'M6') and c['metric'] in ('total_waf', 'C_waf') and 'p' in c]
    for c, h in zip(prim, holm([c['p'] for c in prim])): c['holm_p_4primary'] = h
    for n, rows in (('runs.csv', runs), ('reset_events.csv', rev), ('statistics.csv', stat), ('contrasts.csv', con)): R.write(n, rows)
    for r in runs: print(r['host'], r['policy'], r['rep'], r['valid'], f"{r['total_waf']:.4f}", r.get('resets', ''), r['module_sha256'], r['icat_seed'])
    for c in con:
        if c['metric'] in ('total_waf', 'C_waf', 'C_resets', 'ycsb_throughput', 'C_clat_p99_us_jobmean', 'C_resettle_s_mean'):
            print(c['question'][:12], c['host'], c['contrast'], c['metric'], *(f"{k}={c[k]:.4g}" for k in ('diff', 'ci_lo', 'ci_hi', 'p', 'hedges_g', 'holm_p_4primary', 'paired_mean') if isinstance(c.get(k), float)))
