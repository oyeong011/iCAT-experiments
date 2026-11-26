#!/usr/bin/env python3
"""Pre-registered secondary metrics (abl-20261125 prereg sec. 4) from existing raw logs only; no new runs.
    python3 -I -B analysis/revision/secondary_metrics.py
1 C_first5min_waf : control-series, first sample >= phase-C START .. first sample >= START+300 s (e1_revd.py definition)
2 explore cost    : kernel samples with evaluated != best (best= field of the same sample line): host, gc, WAF, host share
3 adaptation      : per partition, first reset in phase -> next settled of the same partition (s, windows) (r_suite e3);
                    + pre-defined recovery time (recovery.py, TOL 1.05 ROLL 10 HOLD 20) as auxiliary
Every metric is computed twice (existing code path vs. an independent re-implementation here) and compared.
Outputs result/secondary-metrics-20261126/{runs.csv, partition_adaptation.csv, crosscheck.csv, statistics.csv, contrasts.csv}"""
import csv, re, sys, statistics as st
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import greedy_analysis as GA
R = GA.R; ROOT = R.ROOT; ns = R.ns
R.rel = lambda d: str(d.relative_to(ROOT))          # all inputs are 승컴 main
OUT = ROOT / 'result/secondary-metrics-20261126'

SRC = {'revD-v4': 'result/revD-20261124/raw', 'abl-v4': 'result/revision-additional-ablation/raw',
       'abl-nodiscount': 'result/revision-additional-ablation/raw', 'abl-off-elim-settle-drift-probe': 'result/revision-additional-ablation/raw',
       'greedy-online': 'result/greedy-20261125/raw'}
LEARNS_SETTLE = {'revD-v4', 'abl-v4', 'abl-nodiscount'}   # OffBundle (VARIANT 2) and Greedy (VARIANT 8) never settle or reset by design

# ---------------- independent re-implementation (does not call recovery.py / e1_revd / r_suite code)
def ts(p): return datetime.fromisoformat(p.read_text().strip()).timestamp()

def first5_indep(d):
    t0 = ts(d / 'phase-C-start.time'); pts = []
    for l in open(d / 'control-series.txt'):
        f = dict(x.split('=') for x in l.split()[1:]); pts.append((int(l.split()[0]), int(f['host_pages']), int(f['gc_pages'])))
    a = next(x for x in pts if x[0] >= t0); b = next((x for x in pts if x[0] >= t0 + 300), None)
    return 1 + (b[2] - a[2]) / (b[1] - a[1]) if b else None

def klog_indep(d):
    start, samp, ev = {}, [], []
    for l in open(d / 'kernel.log', errors='replace'):
        t = l[1:l.index(']')].strip() if l.startswith('[') else None
        if t is None: continue
        if ' START' in l and 'phase=' in l: start[l.split('phase=')[1][0]] = float(t)
        elif 'WATGC_V2 sample' in l:
            f = dict(x.split('=', 1) for x in l.split() if '=' in x)
            samp.append({'t': float(t), 'part': int(f['part']), 'ev': int(f['evaluated']), 'best': int(f['best']), 'h': int(f['host']), 'g': int(f['gc_pages'])})
        elif 'WATGC_V2 reset' in l or 'WATGC_V2 settled' in l:
            ev.append((float(t), 'reset' if 'reset' in l.split('WATGC_V2 ')[1][:6] else 'settled', int(l.split('part=')[1].split()[0])))
    return start, samp, ev

def explore_cost(samp, lo=0, hi=1e18):
    w = [x for x in samp if lo <= x['t'] < hi]; e = [x for x in w if x['ev'] != x['best']]
    H, G, Ht = sum(x['h'] for x in e), sum(x['g'] for x in e), sum(x['h'] for x in w)
    return {'explore_windows': len(e), 'windows': len(w), 'explore_host_share': H / Ht if Ht else None,
            'explore_waf': 1 + G / H if H else None, 'explore_gc': G}

def adapt_indep(start, samp, ev, ph, t1):
    t0 = start[ph]; rows = []
    for part in range(4):
        rs = sorted(t for t, k, p in ev if k == 'reset' and p == part and t0 <= t < t1)
        if not rs: continue
        s1 = min((t for t, k, p in ev if k == 'settled' and p == part and t > rs[0]), default=None)
        rows.append({'part': part, 'resettle_s': s1 - rs[0] if s1 else None,
                     'windows': sum(1 for x in samp if x['part'] == part and rs[0] < x['t'] <= (s1 or t1))})
    return rows

# ---------------- stats
def desc(xs):
    xs = [x for x in xs if x is not None and x != '']
    return R.desc(xs) if len(xs) == 3 else {'n': len(xs), 'mean': st.mean(xs) if xs else '', 'sd': '', 'ci_lo': '', 'ci_hi': ''}

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True); R.OUT = OUT
    dirs = [d for p, s in SRC.items() for d in sorted((ROOT / s).glob(f'mixFYF-{p}-rep[123]'))]
    old = {r['dir']: r for r in csv.DictReader(open(ROOT / 'result/revD-20261124-analysis/runs.csv'))}
    old_part = {(r['dir'], r['phase'], r['part']): r for r in csv.DictReader(open(ROOT / 'result/revision-20261125-analysis/e3_partition.csv'))}
    prow_ex, rrow_ex = R.e3([('승컴', d) for d in dirs])                         # existing code path
    ex = {r['dir']: r for r in rrow_ex}
    runs, parts, xc = [], [], []
    for d in dirs:
        rel, pol = R.rel(d), R.policy(d); v, why = R.validity(d)
        start, samp, ev = klog_indep(d); t1 = {'B': start['C'], 'C': 1e18}
        r = {'policy': pol, 'rep': R.rep(d), 'dir': rel, 'valid': v, 'invalid_reason': why}
        # 1 first 5 min
        s = ns['series'](d); t0 = dict((p, a) for p, a, b in ns['phases'](d))['C']
        pts = [x for x in s if x[0] >= t0]; j = next((i for i, x in enumerate(pts) if x[0] >= t0 + 300), None)
        r['C_first5min_waf'] = 1 + (pts[j][2] - pts[0][2]) / (pts[j][1] - pts[0][1])
        r['C_first5min_waf_indep'] = first5_indep(d)
        # 2 explore cost (run, phase C)
        for tag, lo, hi in (('run', 0, 1e18), ('C', start['C'], 1e18)):
            r.update({f'{tag}_{k}': v_ for k, v_ in explore_cost(samp, lo, hi).items()})
        # 3 adaptation (existing code values + independent), recovery (aux)
        for ph in 'BC':
            a = adapt_indep(start, samp, ev, ph, t1[ph])
            parts += [{'policy': pol, 'rep': r['rep'], 'phase': ph, **x} for x in a]
            r[f'{ph}_parts_reset'] = len(a)
            r[f'{ph}_resettle_s_max'] = max((x['resettle_s'] for x in a if x['resettle_s'] is not None), default=None)
            r[f'{ph}_resettle_s_mean'] = st.mean([x['resettle_s'] for x in a if x['resettle_s'] is not None]) if any(x['resettle_s'] is not None for x in a) else None
            r[f'{ph}_adapt_windows_sum'] = sum(x['windows'] for x in a) if a else None
            r[f'{ph}_recovery_s_aux'] = ex[rel].get(f'{ph}_recovery_s')
            e = ex[rel]
            xc.append({'dir': rel, 'metric': f'{ph}_parts_reset', 'existing': e[f'{ph}_parts_reset'], 'indep': len(a)})
            xc.append({'dir': rel, 'metric': f'{ph}_explore_windows_sum', 'existing': e[f'{ph}_explore_windows_sum'], 'indep': r[f'{ph}_adapt_windows_sum'] if a else ''})
            xc.append({'dir': rel, 'metric': f'{ph}_resettle_s_max', 'existing': e[f'{ph}_resettle_s_max'], 'indep': r[f'{ph}_resettle_s_max'] if r[f'{ph}_resettle_s_max'] is not None else ''})
            for x in a:   # pushed 11-25 per-partition values (revD only)
                o = old_part.get((rel, ph, str(x['part'])))
                if o: xc.append({'dir': rel, 'metric': f'{ph}_p{x["part"]}_resettle_s vs pushed e3_partition.csv', 'existing': o['resettle_s'], 'indep': x['resettle_s'] if x['resettle_s'] is not None else ''})
        xc.append({'dir': rel, 'metric': 'C_first5min_waf (code path vs indep)', 'existing': r['C_first5min_waf'], 'indep': r['C_first5min_waf_indep']})
        if rel in old: xc.append({'dir': rel, 'metric': 'C_first5min_waf vs pushed revD runs.csv', 'existing': old[rel]['C_first5min_waf'], 'indep': r['C_first5min_waf_indep']})
        r['adaptation_measurable'] = pol in LEARNS_SETTLE
        runs.append(r)
    for x in xc:
        a, b = x['existing'], x['indep']
        x['agree'] = (a in ('', None) and b in ('', None)) or (a not in ('', None) and b not in ('', None) and abs(float(a) - float(b)) < 1e-6)
    KEYS = ['C_first5min_waf', 'run_explore_windows', 'run_explore_host_share', 'run_explore_waf', 'C_explore_windows', 'C_explore_host_share', 'C_explore_waf',
            'B_parts_reset', 'C_parts_reset', 'C_resettle_s_mean', 'C_resettle_s_max', 'C_adapt_windows_sum', 'C_recovery_s_aux']
    stat = [{'policy': p, 'metric': k, 'values_rep1_2_3': ' / '.join('' if r[k] is None else f'{r[k]:.4f}' for r in runs if r['policy'] == p), **desc([r[k] for r in runs if r['policy'] == p])}
            for p in SRC for k in KEYS]
    con = []
    for b, a in [('abl-nodiscount', 'abl-v4'), ('abl-off-elim-settle-drift-probe', 'abl-v4'), ('greedy-online', 'revD-v4'), ('greedy-online', 'abl-v4')]:
        for k in KEYS:
            va, vb = [r[k] for r in runs if r['policy'] == a], [r[k] for r in runs if r['policy'] == b]
            ok = all(x is not None for x in va + vb) and len(va) == len(vb) == 3 and (st.variance(va) + st.variance(vb)) > 0
            con.append({'contrast': f'{b} - {a}', 'metric': k, **(GA.welch(va, vb) if ok else {'diff': 'not measurable (structurally absent or zero variance)'})})
    for n, rows in (('runs.csv', runs), ('partition_adaptation.csv', parts), ('crosscheck.csv', xc), ('statistics.csv', stat), ('contrasts.csv', con)):
        R.write(n, rows)
    print('crosscheck:', sum(x['agree'] for x in xc), '/', len(xc), 'agree')
    for x in xc:
        if not x['agree']: print('  MISMATCH', x)
    for s_ in stat:
        if s_['metric'] in ('C_first5min_waf', 'run_explore_host_share', 'run_explore_waf', 'C_explore_waf', 'C_resettle_s_mean', 'C_adapt_windows_sum', 'C_recovery_s_aux'):
            print(s_['policy'][:14], s_['metric'], s_['values_rep1_2_3'], str(s_['mean'])[:7], str(s_['sd'])[:6])
    for c in con:
        if isinstance(c['diff'], float): print(c['contrast'][:30], c['metric'], f"{c['diff']:+.4f} [{c['ci_lo']:+.4f}, {c['ci_hi']:+.4f}] p={c['p']:.3f}")
