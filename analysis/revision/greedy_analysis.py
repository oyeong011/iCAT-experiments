#!/usr/bin/env python3
"""greedy-20261125 analysis (pre-registered in result/greedy-20261125/preregistration.md). Run only after the queue ends.
    python3 -I -B analysis/revision/greedy_analysis.py [GOCOM_DIR]
GOCOM_DIR (optional) = git archive of origin/report/data-validity-20261124 result/revA-20261114 (Random Selection, 고컴 only;
reported as a separate-host reference row, never pooled).
Outputs result/greedy-20261125-analysis/{runs.csv, arm_counts.csv, greedy_rule_check.csv, statistics.csv, contrasts.csv}"""
import re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r_suite_20261125 as R                      # validity, klog, counters, desc, write (11-25 reanalysis helpers)
import statistics as st
from scipy import stats

ROOT = R.ROOT; G = ROOT / 'result/greedy-20261125'; OUT = ROOT / 'result/greedy-20261125-analysis'
ARMS = range(15, 60)                              # WATGC_V2_ARM_LO..ARM_N-1 (45 arms)
CONTROL = (G / 'control.txt').read_text().split()[0] if (G / 'control.txt').exists() else None   # set by the pre-registered rule

def wq16(h, g): return 65536 + g * 65536 // h  # watgc_v2_waf_q16: 1 + gc/host, Q16, floor

def run_row(d, host='승컴'):
    r = {'host': host, 'policy': R.policy(d), 'rep': R.rep(d), 'dir': R.rel(d) if R.SEUNG in d.parents else str(d.relative_to(ROOT))}
    r['valid'], r['invalid_reason'] = R.validity(d)
    for p in 'ABC':
        (sh, sg), _ = R.counters(d / f'phase-{p}-start.txt'); (eh, eg), _ = R.counters(d / f'phase-{p}-end.txt')
        r[f'{p}_waf'] = 1 + (eg - sg) / (eh - sh); r[f'{p}_host'] = eh - sh
    (th, tg), (ph, pg) = R.counters(d / 'stopped.txt'); r['total_waf'] = 1 + tg / th; r['waf_paths_agree'] = abs(tg / th - pg / ph) < 1e-9
    import gzip
    y = gzip.open(d / 'ycsb-run-B.txt.gz', 'rt', errors='replace').read()
    r['ycsb_ops'] = sum(map(int, re.findall(r'^\[(?:READ|UPDATE)\], Operations, (\d+)', y, re.M)))
    r['ycsb_ok'] = sum(map(int, re.findall(r'^\[(?:READ|UPDATE)\], Return=OK, (\d+)', y, re.M)))
    r['ycsb_success'] = r['ycsb_ok'] / r['ycsb_ops'] if r['ycsb_ops'] else 0; r['sqlite_full'] = y.count('SQLITE_FULL')
    kl = (d / 'kernel.log').read_text(errors='replace')
    last = {}
    for m in re.finditer(r'WATGC_V2 sample .*part=(\d) .*select=(\d+) eval_explore=(\d+) elim=(\d+) best_change=(\d+) reset=(\d+) .*learner_ns=(\d+)', kl):
        last[int(m[1])] = tuple(map(int, m.groups()[1:]))
    for i, k in enumerate(['switches', 'eval_explore', 'elim', 'best_change', 'resets', 'learner_ns']):
        r[k] = sum(v[i] for v in last.values())
    r['learner_ms'] = r.pop('learner_ns') / 1e6
    r['settled_events'] = len(re.findall(r'WATGC_V2 settled', kl))
    return r

def samples(d):
    out = []
    for m in re.finditer(r'WATGC_V2 sample .*part=(\d) epoch=\d+ window=(\d+) .*evaluated=(\d+) .*host=(\d+) gc_pages=(\d+) .*next=(\d+)', (d / 'kernel.log').read_text(errors='replace')):
        out.append(tuple(map(int, m.groups())))
    return out

def learner(d, pol, rep):
    """per-arm counts, final arm, initial exploration cost and (greedy only) an exact replay of the selection rule."""
    arms, chk = [], []
    s = samples(d)
    for part in range(4):
        w = [x for x in s if x[0] == part]
        ev, nx = Counter(x[2] for x in w), Counter(x[5] for x in w)
        arms += [{'policy': pol, 'rep': rep, 'part': part, 'arm': a, 'evaluated_windows': ev[a], 'selected_next': nx[a]} for a in ARMS]
        H, Gc, seen, bad, first = Counter(), Counter(), set(), 0, None
        for _, win, a, h, g, nxt in w:
            H[a] += h; Gc[a] += g; seen.add(a)
            if len(seen) == len(ARMS):
                first = first or win
                exp = min(ARMS, key=lambda i: (wq16(H[i], Gc[i]), i))   # lowest mean, ties -> lowest index
                bad += nxt != exp
        init = [x for x in w if first and x[1] <= first]
        chk.append({'policy': pol, 'rep': rep, 'part': part, 'windows': len(w), 'coverage_window': first,
                    'init_host': sum(x[3] for x in init), 'init_gc': sum(x[4] for x in init),
                    'init_waf': 1 + sum(x[4] for x in init) / max(sum(x[3] for x in init), 1),
                    'distinct_first45': len({x[2] for x in w[:45]}), 'final_arm': w[-1][5] if w else '',
                    'greedy_rule_mismatches': bad if pol == 'greedy-online' else ''})
    return arms, chk

def welch(a, b):   # b - a
    va, vb = st.variance(a) / len(a), st.variance(b) / len(b); dlt = st.mean(b) - st.mean(a)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)); h = stats.t.ppf(.975, df) * (va + vb) ** .5
    sp = (((len(a) - 1) * st.variance(a) + (len(b) - 1) * st.variance(b)) / (len(a) + len(b) - 2)) ** .5
    t = dlt / (va + vb) ** .5
    return {'diff': dlt, 'ci_lo': dlt - h, 'ci_hi': dlt + h, 'welch_df': df, 'p': 2 * stats.t.sf(abs(t), df),
            'hedges_g': dlt / sp * (1 - 3 / (4 * (len(a) + len(b)) - 9)) if sp else float('nan')}

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True); R.OUT = OUT
    dirs = sorted(G.glob('raw/mixFYF-greedy-*-rep[123]'))
    ctrl_dirs = {'abl-v4': sorted((ROOT / 'result/revision-additional-ablation/raw').glob('mixFYF-abl-v4-rep[123]')),
                 'revD-v4': sorted((ROOT / 'result/revD-20261124/raw').glob('mixFYF-revD-v4-rep[123]'))}
    if CONTROL == 'greedy-v4': ctrl = [d for d in dirs if R.policy(d) == 'greedy-v4']
    else: ctrl = ctrl_dirs.get(CONTROL, [])
    runs = [run_row(d) for d in dirs + (ctrl if CONTROL != 'greedy-v4' else [])]
    arms, chk = [], []
    for d in dirs + (ctrl if CONTROL != 'greedy-v4' else []):
        a, c = learner(d, R.policy(d), R.rep(d)); arms += a; chk += c
    for name, rows in (('runs.csv', runs), ('arm_counts.csv', arms), ('greedy_rule_check.csv', chk)):
        R.write(name, rows)
    v = lambda pol, k: [r[k] for r in runs if r['policy'] == pol and r['valid']]
    ctl = 'greedy-v4' if CONTROL == 'greedy-v4' else CONTROL
    keys = ['total_waf', 'A_waf', 'B_waf', 'C_waf', 'switches', 'eval_explore', 'learner_ms', 'ycsb_ops']
    R.write('statistics.csv', [{'policy': p, 'metric': k, 'values': ' / '.join(f'{x:.4f}' for x in v(p, k)), **R.desc(v(p, k))} for p in ('greedy-online', ctl) for k in keys])
    con = []
    for k in ('total_waf', 'C_waf'):
        a, b = v(ctl, k), v('greedy-online', k)
        if len(a) == 3 and len(b) == 3:
            pa = {r['rep']: r[k] for r in runs if r['policy'] == ctl and r['valid']}; pb = {r['rep']: r[k] for r in runs if r['policy'] == 'greedy-online' and r['valid']}
            dd = [pb[i] - pa[i] for i in (1, 2, 3)]; m, s = st.mean(dd), st.stdev(dd); h = stats.t.ppf(.975, 2) * s / 3 ** .5
            con.append({'host': '승컴', 'contrast': f'greedy-online - {ctl}', 'metric': k, **welch(a, b),
                        'paired_mean': m, 'paired_ci_lo': m - h, 'paired_ci_hi': m + h, 'paired_p': 2 * stats.t.sf(abs(m / (s / 3 ** .5)), 2) if s else float('nan')})
        else: con.append({'host': '승컴', 'contrast': f'greedy-online - {ctl}', 'metric': k, 'diff': 'n<3: no statistics'})
    if R.GOCOM:   # separate host reference: 고컴 Random Selection vs 고컴 V4 (measured), never pooled with 승컴
        gr = {p: [float(re.search(r'^total .*WAF=([\d.]+)', (dd / 'summary.txt').read_text(), re.M)[1]) for dd in sorted(R.GOCOM.glob(f'mixFYF-{p}-rep[123]')) if R.validity(dd)[0]] for p in ('revA-v4', 'revA-random')}
        con.append({'host': '고컴 (참고, 합산 안 함)', 'contrast': 'revA-random - revA-v4', 'metric': 'total_waf', **welch(gr['revA-v4'], gr['revA-random'])})
    R.write('contrasts.csv', con)
    for r in runs: print(r['policy'], r['rep'], r['valid'], f"{r['total_waf']:.4f}", r['switches'])
    for c in con: print(c)
