#!/usr/bin/env python3
"""11-25 reanalysis of EXISTING raw logs only (no new runs). 승컴 and 고컴 are never pooled: every row has a `host` column
and every statistic is computed within one host and one policy.

Usage:  python3 -I -B analysis/revision/r_suite_20261125.py GOCOM_DIR
  GOCOM_DIR = `git archive origin/report/data-validity-20261124 result/revA-20261114 | tar -x -C GOCOM_DIR` (see README.md)
Outputs: result/revision-20261125-analysis/*.csv   (each row carries the raw run dir + valid flag)
  1 waf_recalc.csv      phase/total WAF from raw counters by two paths (control total line, per-partition sum) vs summary.txt
  3 e3_partition.csv    per run x phase x partition: first reset, reset->own-partition settle (s, windows); e3_run.csv per run
  4 gamma.csv           windows per partition and the discount weight gamma^n of the oldest data still in the learner
  5 latency.csv         FIO write clat (per job) and YCSB READ/UPDATE latency per run; latency_stats.csv (descriptive only)
  6 random_search.csv   [측정] 고컴 revA totals and [추정] Random Search expectation built from 고컴 revA random-selection windows
"""
import csv, gzip, json, random, re, statistics as st, sys
from collections import defaultdict
from pathlib import Path
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'result/revision-20261125-analysis'
SEUNG = ROOT / 'result/revD-20261124/raw'
GOCOM = Path(sys.argv[1]) / 'result/revA-20261114/raw' if len(sys.argv) > 1 else None
GAMMA = 65503 / 65536                                    # WATGC_V2_GAMMA_Q16, applied to ALL arms every window (conv_ftl.c:582-587)
sys.path.insert(0, str(ROOT / 'analysis/revision'))
from e1_revd import ns                                   # pre-registered recovery definition (TOL 1.05, ROLL 10, HOLD 20)

def runs():
    out = [('승컴', d) for d in sorted(SEUNG.glob('mixFYF-revD-*-rep[123]'))]
    if GOCOM: out += [('고컴', d) for d in sorted(GOCOM.glob('mixFYF-*-rep[123]'))]
    return out

def rel(d):   # raw path: 승컴 = repo main, 고컴 = branch@commit (README.md)
    return str(d.relative_to(ROOT)) if SEUNG in d.parents else 'origin/report/data-validity-20261124@299d6e78d:result/revA-20261114/raw/' + d.name

def policy(d): return re.match(r'mixFYF-(.+)-rep\d$', d.name)[1]
def rep(d): return int(d.name[-1])

def counters(p):                                         # first line = control total, part= lines = partitions
    t = p.read_text().splitlines()
    tot = tuple(int(re.search(rf'\b{k}=(\d+)', t[0])[1]) for k in ('host_pages', 'gc_pages'))
    parts = [(int(h), int(g)) for h, g in re.findall(r'part=\d host_pages=(\d+) gc_pages=(\d+)', '\n'.join(t[1:]))]
    return tot, (sum(h for h, _ in parts), sum(g for _, g in parts))

def validity(d):
    bad = []
    if (d / 'exit-code.txt').read_text().strip() != '0': bad.append('exit!=0')
    for p in 'ABC':
        if not (d / f'phase-{p}-end.txt').exists(): bad.append(f'phase {p} missing')
    txt = gzip.open(d / 'ycsb-run-B.txt.gz', 'rt', errors='replace').read() if (d / 'ycsb-run-B.txt.gz').exists() else ''
    ops = sum(map(int, re.findall(r'^\[(?:READ|UPDATE)\], Operations, (\d+)', txt, re.M)))
    ok = sum(map(int, re.findall(r'^\[(?:READ|UPDATE)\], Return=OK, (\d+)', txt, re.M)))
    if not ops or ok != ops or 'SQLITE_FULL' in txt: bad.append(f'ycsb ok={ok}/{ops}')
    if re.search(r'BUG:|WARNING:|Oops|Call Trace', (d / 'kernel.log').read_text(errors='replace')): bad.append('kernel error')
    return not bad, '; '.join(bad)

def klog(d):
    """phase START times, samples (t, part, window, evaluated, host, gc, settled) and events (t, kind, part)."""
    start, samp, ev = {}, [], []
    for l in (d / 'kernel.log').read_text(errors='replace').splitlines():   # gate 1 (11-25): no window gaps in any run
        if (m := re.match(r'\[\s*([\d.]+)\].*phase=(\w) START', l)): start[m[2]] = float(m[1]); continue
        if (m := re.match(r'\[\s*([\d.]+)\] NVMeVirt: WATGC_V2 sample .*part=(\d) epoch=\d+ window=(\d+) .*evaluated=(\d+) .*host=(\d+) gc_pages=(\d+) .*settled=(\d)', l)):
            samp.append((float(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), int(m[6]), int(m[7])))
        elif (m := re.match(r'\[\s*([\d.]+)\] NVMeVirt: WATGC_V2 (reset|settled) .*part=(\d)', l)):
            ev.append((float(m[1]), m[2], int(m[3])))
    return start, samp, ev

def phase_of(start, t):
    ps = [p for p in sorted(start, key=start.get) if start[p] <= t]
    return ps[-1] if ps else None

def write(name, rows):
    with open(OUT / name, 'w', newline='') as f:
        w = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r)), lineterminator='\n'); w.writeheader(); w.writerows(rows)

def desc(xs):                                            # mean, SD, t 95% CI; only for n=3 valid runs
    if len(xs) != 3: return {'n': len(xs), 'mean': '', 'sd': '', 'ci_lo': '', 'ci_hi': ''}
    m, s = st.mean(xs), st.stdev(xs); h = stats.t.ppf(.975, 2) * s / 3 ** .5
    return {'n': 3, 'mean': m, 'sd': s, 'ci_lo': m - h, 'ci_hi': m + h}

def stat_rows(rows, keys, group=('host', 'policy')):
    g = defaultdict(list)
    for r in rows:
        if r['valid']: g[tuple(r[k] for k in group)].append(r)
    return [{**dict(zip(group, k)), 'metric': m, 'values': ' / '.join(f'{r[m]:.4g}' for r in v if r.get(m) not in (None, '')),
             **desc([r[m] for r in v if r.get(m) not in (None, '')])} for k, v in sorted(g.items()) for m in keys]

# ---------------------------------------------------------------- 1 WAF recompute
def waf_recalc(all_runs):
    rows = []
    for host, d in all_runs:
        if host != '승컴': continue
        r = {'host': host, 'policy': policy(d), 'rep': rep(d), 'dir': rel(d)}
        r['valid'], r['invalid_reason'] = validity(d)
        z0, zp = counters(d / 'started.txt'); r['started_zero'] = z0 == (0, 0) and zp == (0, 0)
        summ = (d / 'summary.txt').read_text()
        for p, tag in (('A', 'phaseA'), ('B', 'phaseB'), ('C', 'phaseC')):
            (sh, sg), (sph, spg) = counters(d / f'phase-{p}-start.txt'); (eh, eg), (eph, epg) = counters(d / f'phase-{p}-end.txt')
            r[f'{p}_host'], r[f'{p}_gc'] = eh - sh, eg - sg
            r[f'{p}_waf_total_line'] = 1 + (eg - sg) / (eh - sh)
            r[f'{p}_waf_part_sum'] = 1 + (epg - spg) / (eph - sph)
            r[f'{p}_waf_summary'] = float(re.search(rf'{tag}\(\S+\) .*WAF=([\d.]+)', summ)[1])
        (th, tg), (tph, tpg) = counters(d / 'stopped.txt'); (fh, fg), (fph, fpg) = counters(d / 'final-control.txt')
        r['total_waf_stopped'], r['total_waf_final_part_sum'] = 1 + tg / th, 1 + fpg / fph
        r['total_waf_summary'] = float(re.search(r'^total .*WAF=([\d.]+)', summ, re.M)[1])
        r['paths_agree_1e-6'] = all(abs(r[a] - r[b]) < 1e-6 for p in 'ABC' for a, b in
                                    ((f'{p}_waf_total_line', f'{p}_waf_part_sum'), (f'{p}_waf_total_line', f'{p}_waf_summary'))) \
            and abs(r['total_waf_stopped'] - r['total_waf_final_part_sum']) < 1e-6 and abs(r['total_waf_stopped'] - r['total_waf_summary']) < 1e-6
        rows.append(r)
    return rows

# ---------------------------------------------------------------- 3 E3 per partition (preregistration metric 4/5 definition)
def e3(all_runs):
    prow, rrow = [], []
    for host, d in all_runs:
        pol = policy(d)
        if 'arm47' in pol: continue                        # fixed arm: no learner
        v, why = validity(d); start, samp, ev = klog(d)
        ends = {p: e for p, e in zip(sorted(start, key=start.get), sorted(start.values())[1:] + [1e18])}
        run = {'host': host, 'policy': pol, 'rep': rep(d), 'valid': v, 'invalid_reason': why, 'dir': rel(d)}
        for ph in 'BC':
            t0, t1 = start[ph], ends[ph]
            for part in range(4):
                rs = [t for t, k, p in ev if k == 'reset' and p == part and t0 <= t < t1]
                settled_entry = [x for x in samp if x[1] == part and x[0] < t0]
                r = {'host': host, 'policy': pol, 'rep': rep(d), 'phase': ph, 'part': part, 'valid': v, 'dir': rel(d),
                     'settled_at_phase_start': settled_entry[-1][6] if settled_entry else '', 'resets': len(rs)}
                if rs:
                    r0 = rs[0]; s1 = [t for t, k, p in ev if k == 'settled' and p == part and t > r0]
                    r['detect_s'] = r0 - t0                  # metric 3/4: reset = re-exploration start
                    r['resettle_s'] = s1[0] - r0 if s1 else ''
                    r['explore_windows'] = sum(1 for x in samp if x[1] == part and r0 < x[0] <= (s1[0] if s1 else t1))   # metric 5, own partition only
                    r['resettled_in_phase'] = bool(s1 and s1[0] < t1)
                prow.append(r)
            pr = [x for x in prow if x['dir'] == rel(d) and x['phase'] == ph and 'detect_s' in x]
            run[f'{ph}_parts_reset'] = len(pr)
            run[f'{ph}_first_detect_s'] = min((x['detect_s'] for x in pr), default='')
            run[f'{ph}_explore_windows_sum'] = sum(x['explore_windows'] for x in pr) if pr else ''
            run[f'{ph}_resettle_s_max'] = max((x['resettle_s'] for x in pr if x['resettle_s'] != ''), default='')
            run[f'{ph}_parts_resettled'] = sum(1 for x in pr if x['resettled_in_phase'])
        if v:
            s = ns['series'](d); ph = {p: (a, b) for p, a, b in ns['phases'](d)}
            for p in 'BC':
                ref, rec, pw = ns['recovery'](s, *ph[p])
                run[f'{p}_recovery_s'], run[f'{p}_ref_waf_2nd_half'], run[f'{p}_recovery2_s'] = rec[0], ref, rec[2]
        rrow.append(run)
    return prow, rrow

# ---------------------------------------------------------------- 4 discount weight
def gamma(all_runs):
    rows = []
    for host, d in all_runs:
        if 'arm47' in policy(d): continue
        start, samp, ev = klog(d); v, why = validity(d)
        for part in range(4):
            w = [x for x in samp if x[1] == part]
            last_reset = max((t for t, k, p in ev if k == 'reset' and p == part), default=None)
            since = sum(1 for x in w if last_reset is None or x[0] > last_reset)
            perph = {ph: sum(1 for x in w if phase_of(start, x[0]) == ph) for ph in 'ABC'}
            rows.append({'host': host, 'policy': policy(d), 'rep': rep(d), 'part': part, 'valid': v, 'invalid_reason': why, 'windows_total': len(w),
                         **{f'windows_{k}': v for k, v in perph.items()}, 'windows_since_last_reset': since,
                         'weight_oldest_window_at_end': GAMMA ** len(w),          # if never reset
                         'weight_oldest_since_reset': GAMMA ** since,
                         'weight_phaseA_end_at_run_end': GAMMA ** (perph['B'] + perph['C']),
                         'dir': rel(d)})
    return rows

# ---------------------------------------------------------------- 5 latency
def latency(all_runs):
    rows = []
    for host, d in all_runs:
        v, why = validity(d); r = {'host': host, 'policy': policy(d), 'rep': rep(d), 'valid': v, 'invalid_reason': why, 'dir': rel(d)}
        for ph in 'AC':
            for j in json.load(open(d / f'phase-{ph}.json'))['jobs']:
                c = j['write']['clat_ns']; pc = c['percentile']
                r[f'{ph}_{j["jobname"]}_err'] = j['error']
                r[f'{ph}_{j["jobname"]}_clat_mean_us'] = c['mean'] / 1e3
                for q, k in (('50.000000', 'p50'), ('99.000000', 'p99'), ('99.900000', 'p99.9')):
                    r[f'{ph}_{j["jobname"]}_clat_{k}_us'] = pc[q] / 1e3
        txt = gzip.open(d / 'ycsb-run-B.txt.gz', 'rt', errors='replace').read()
        r['ycsb_throughput'] = float(re.search(r'^\[OVERALL\], Throughput\(ops/sec\), ([\d.]+)', txt, re.M)[1])
        for op in ('READ', 'UPDATE'):
            for k, lab in (('AverageLatency', 'avg'), ('95thPercentileLatency', 'p95'), ('99thPercentileLatency', 'p99')):
                r[f'ycsb_{op}_{lab}_us'] = float(re.search(rf'^\[{op}\], {k}\(us\), ([\d.]+)', txt, re.M)[1])
        rows.append(r)
    return rows

# ---------------------------------------------------------------- 6 Random Search estimate from random-selection windows
def random_search(all_runs, trials=20000, seed=20261125):
    gr = [(h, d) for h, d in all_runs if h == '고컴']
    used = []; win = defaultdict(list)                               # (phase, arm) -> [(host, gc)] per window; host/gc are per-window deltas
    for _, d in gr:
        if policy(d) != 'revA-random' or not validity(d)[0]: continue
        used.append(rel(d))
        start, samp, _ = klog(d)
        for t, part, _, arm, h, g, _ in samp:
            win[(phase_of(start, t), arm)].append((h, g))
    est = lambda ph, a: 1 + sum(g for _, g in win[(ph, a)]) / sum(h for h, _ in win[(ph, a)])
    arms = sorted({a for p, a in win if p == 'A'} & {a for p, a in win if p == 'C'})
    hB = [x for (p, _), v in win.items() if p == 'B' for x in v]; wafB = 1 + sum(g for _, g in hB) / sum(h for h, _ in hB)   # B sparse: pooled
    meas = {}
    for _, d in gr:
        s = (d / 'summary.txt').read_text(); meas.setdefault(policy(d), []).append(
            (validity(d)[0], {k: float(re.search(rf'^{k}.*WAF=([\d.]+)', s, re.M)[1]) for k in ('total', 'phaseA', 'phaseB', 'phaseC')}, rel(d)))
    a47 = meas['arm47'][0][1]
    H = {k: float(re.search(rf'^{k}\S* host_pages=(\d+)', (GOCOM / 'mixFYF-arm47-rep1/summary.txt').read_text(), re.M)[1]) for k in ('phaseA', 'phaseB', 'phaseC')}
    tot = lambda a: (H['phaseA'] * est('A', a) + H['phaseB'] * wafB + H['phaseC'] * est('C', a)) / sum(H.values())
    rows = [{'kind': '[측정]', 'host': '고컴', 'what': f'{p} total WAF', 'n': len(v), 'valid_n': sum(x[0] for x in v),
             'value': st.mean(x[1]['total'] for x in v if x[0]), 'values': ' / '.join(f"{x[1]['total']:.4f}" for x in v), 'source': ' ; '.join(x[2] for x in v)}
            for p, v in sorted(meas.items())]
    rows.append({'kind': '[보정]', 'host': '고컴', 'what': 'arm47 estimate - measured (phase A / C / total)', 'n': 1,
                 'value': tot(47) - a47['total'], 'values': f"{est('A', 47) - a47['phaseA']:+.4f} / {est('C', 47) - a47['phaseC']:+.4f} / {tot(47) - a47['total']:+.4f}",
                 'source': 'estimator(arm47) vs mixFYF-arm47-rep1/summary.txt'})
    best = min(arms, key=tot)
    rows.append({'kind': '[추정]', 'host': '고컴', 'what': f'best single fixed arm in hindsight (arm {best})', 'n': '', 'value': tot(best), 'values': '', 'source': 'per-arm window estimate'})
    # Random Search: per partition, try k distinct random arms for one window each at the start of phase A (observation = one
    # random window of that arm in phase A), then fix the arm with the lowest observed WAF for the rest of the run.
    rng = random.Random(seed); obsA = {a: [1 + g / h for h, g in win[('A', a)]] for a in arms}; WIN = 131072
    hpart = sum(H.values()) / 4
    for k in (1, 2, 3, 5, 8, 12, 20, 30, len(arms)):
        vals = []
        for _ in range(trials):
            tried = rng.sample(arms, k); pick = min(tried, key=lambda a: rng.choice(obsA[a]))
            trial = sum(est('A', a) for a in tried) * WIN       # trial windows run at each tried arm's phase-A WAF
            vals.append((trial + (hpart - k * WIN) * tot(pick)) / hpart)
        rows.append({'kind': '[추정]', 'host': '고컴', 'what': f'Random Search k={k} (try k arms x 1 window, then fix)', 'n': trials,
                     'value': st.mean(vals), 'values': f'p10={sorted(vals)[trials // 10]:.4f} p90={sorted(vals)[9 * trials // 10]:.4f}',
                     'source': f'seed={seed}; windows from revA-random rep1-3'})
    src = ' ; '.join(used)
    armrows = [{'arm': a, 'A_windows': len(win[('A', a)]), 'A_waf_est': est('A', a), 'C_windows': len(win[('C', a)]), 'C_waf_est': est('C', a),
                'B_waf_pooled': wafB, 'total_waf_est': tot(a), 'kind': '[추정]', 'valid_runs_used': src} for a in arms]
    return rows, armrows

if __name__ == '__main__':
    assert GOCOM and GOCOM.is_dir(), 'pass the 고컴 archive dir (README.md)'
    OUT.mkdir(exist_ok=True); R = runs()
    w = waf_recalc(R); write('waf_recalc.csv', w)
    assert all(r['started_zero'] and r['paths_agree_1e-6'] for r in w), 'WAF paths disagree'
    p, r = e3(R); write('e3_partition.csv', p); write('e3_run.csv', r)
    write('e3_stats.csv', stat_rows(r, ['C_first_detect_s', 'C_parts_reset', 'C_explore_windows_sum', 'C_resettle_s_max', 'C_recovery_s', 'C_recovery2_s',
                                        'B_first_detect_s', 'B_parts_reset', 'B_recovery_s']))
    write('gamma.csv', gamma(R))
    lat = latency(R); write('latency.csv', lat)
    write('latency_stats.csv', stat_rows(lat, [k for k in lat[0] if k.endswith('_us') or k == 'ycsb_throughput']))
    rs, ar = random_search(R); write('random_search.csv', rs); write('random_search_arms.csv', ar)
    print(len(w), 'waf rows OK;', len(r), 'E3 runs;', len(lat), 'latency runs;', len(rs), 'random-search rows')
