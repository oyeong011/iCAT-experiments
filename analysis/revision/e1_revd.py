#!/usr/bin/env python3
"""E1 revD-20261124 analysis, exactly as pre-registered in result/revD-20261124/preregistration.md.

Recovery/detection definitions are taken verbatim from analysis/revision/recovery.py (functions are extracted with
ast, not copied, so they cannot drift). Statistics only for policies with 3 valid independent runs.
Usage: python3 -I analysis/revision/e1_revd.py   -> result/revD-20261124-analysis/{runs.csv,stats.csv,contrasts.csv}
"""
import ast, csv, gzip, re, statistics as st, sys
from pathlib import Path
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'result/revD-20261124/raw'
OUT = ROOT / 'result/revD-20261124-analysis'
POL = ['revD-v4', 'revD-nodrift', 'revD-fullreset']

# --- pre-registered definitions from recovery.py (TOL, ROLL, HOLD, phases, series, recovery, events) ---
src = (ROOT / 'analysis/revision/recovery.py').read_text()
ns = {'re': re, 'datetime': __import__('datetime').datetime}
for node in ast.parse(src).body:
    keep = isinstance(node, ast.FunctionDef) and node.name in ('phases', 'series', 'recovery', 'events')
    keep |= isinstance(node, ast.Assign) and any(isinstance(t, ast.Tuple) and {e.id for e in t.elts} == {'TOL', 'ROLL', 'HOLD'} for t in node.targets)
    keep |= isinstance(node, ast.Assign) and any(getattr(t, 'id', '') == 'iso' for t in node.targets)
    if keep: exec(compile(ast.Module([node], []), 'recovery.py', 'exec'), ns)
assert (ns['TOL'], ns['ROLL'], ns['HOLD']) == (1.05, 10, 20)

field = lambda t, k: int(re.search(rf'\b{k}=(\d+)', t)[1])
first = lambda p: p.read_text().splitlines()[0]

def run_row(d):
    pol, rep = re.match(r'mixFYF-(revD-\w+)-rep(\d)$', d.name).groups()
    r = {'policy': pol, 'rep': int(rep), 'dir': str(d.relative_to(ROOT))}
    ec = (d / 'exit-code.txt').read_text().strip() if (d / 'exit-code.txt').exists() else 'missing'
    r['exit'] = ec
    bad = [] if ec == '0' else [f'exit={ec}']
    for p in 'ABC':
        s, e = d / f'phase-{p}-start.txt', d / f'phase-{p}-end.txt'
        if not e.exists(): bad.append(f'phase {p} missing'); continue
        h = field(first(e), 'host_pages') - field(first(s), 'host_pages'); g = field(first(e), 'gc_pages') - field(first(s), 'gc_pages')
        r[f'{p}_host'], r[f'{p}_gc'], r[f'{p}_waf'] = h, g, 1 + g / h
        r[f'{p}_start'] = (d / f'phase-{p}-start.time').read_text().strip(); r[f'{p}_end'] = (d / f'phase-{p}-end.time').read_text().strip()
    if (d / 'stopped.txt').exists():
        t = first(d / 'stopped.txt'); r['total_host'], r['total_gc'] = field(t, 'host_pages'), field(t, 'gc_pages')
        r['total_waf'] = 1 + r['total_gc'] / r['total_host']
    y = d / 'ycsb-run-B.txt.gz'
    if y.exists():
        txt = gzip.open(y, 'rt', errors='replace').read()
        ops = sum(int(x) for x in re.findall(r'^\[(?:READ|UPDATE)\], Operations, (\d+)', txt, re.M))
        ok = sum(int(x) for x in re.findall(r'^\[(?:READ|UPDATE)\], Return=OK, (\d+)', txt, re.M))
        r['ycsb_ops'], r['ycsb_ok'] = ops, ok
        r['ycsb_success'] = ok / ops if ops else 0
        r['sqlite_full'] = txt.count('SQLITE_FULL')
        if r['sqlite_full'] or ok != ops or not ops: bad.append(f'YCSB ok={ok}/{ops} sqlite_full={r["sqlite_full"]}')
    else: bad.append('ycsb log missing')
    kl = (d / 'kernel.log').read_text(errors='replace') if (d / 'kernel.log').exists() else ''
    if re.search(r'BUG:|WARNING:|Oops|Call Trace', kl): bad.append('kernel error')
    # metrics 2-8 for phase C (transition FIO-Fast -> after YCSB-A)
    if not bad:
        s = ns['series'](d); ph = {p: (t0, t1) for p, t0, t1 in ns['phases'](d)}
        t0, t1 = ph['C']
        ref, rec, _ = ns['recovery'](s, t0, t1)
        pts = [x for x in s if x[0] >= t0]; j = next((i for i, x in enumerate(pts) if x[0] >= t0 + 300), None)
        r['C_first5min_waf'] = 1 + (pts[j][2] - pts[0][2]) / (pts[j][1] - pts[0][1]) if j else None
        r['C_recovery_s'], r['C_recovery_first_window'], r['C_recovery2_s'] = rec[0], rec[1], rec[2]
        e = ns['events'](d).get('C', {})
        r['C_resets'], r['C_detect_s'], r['C_resettle_s'], r['C_explore_windows'] = e.get('resets'), e.get('detect_s'), e.get('resettle_s'), e.get('explore_windows')
        # 7, 8: per-partition counters from the last WATGC_V2 sample before phase C START and the last before END
        mk = {m[2]: float(m[1]) for m in re.finditer(r'^\[\s*([\d.]+)\].*phase=(\w) (?:START|END)', kl, re.M) if True}
        cs = re.search(r'^\[\s*([\d.]+)\].*phase=C START', kl, re.M); ce = re.search(r'^\[\s*([\d.]+)\].*phase=C END', kl, re.M)
        samp = [(float(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), int(m[6])) for m in re.finditer(
            r'^\[\s*([\d.]+)\] NVMeVirt: WATGC_V2 sample .*part=(\d) .*active=(\d+) revA .*elim=(\d+) .*reset=(\d+) .*learner_ns=(\d+)', kl, re.M)]
        def at(t):
            last = {}
            for x in samp:
                if x[0] <= t: last[x[1]] = x
            return last
        a, b = at(float(cs[1])), at(float(ce[1]))
        r['C_elim'] = sum(b[p][3] - a[p][3] for p in b if p in a)
        r['C_learner_ms'] = sum(b[p][5] - a[p][5] for p in b if p in a) / 1e6
        restored = 0   # metric 7b: active after the first sample following each reset minus active just before it
        for m in re.finditer(r'^\[\s*([\d.]+)\] NVMeVirt: WATGC_V2 reset .*part=(\d)', kl, re.M):
            t, p = float(m[1]), int(m[2])
            if not float(cs[1]) <= t <= float(ce[1]): continue
            pre = [x for x in samp if x[1] == p and x[0] < t]; post = [x for x in samp if x[1] == p and x[0] > t]
            if pre and post: restored += post[0][2] - pre[-1][2]
        r['C_restored_arms'] = restored
    r['valid'] = not bad; r['invalid_reason'] = '; '.join(bad)
    return r

def ci(xs):
    m, s = st.mean(xs), st.stdev(xs); h = stats.t.ppf(.975, len(xs) - 1) * s / len(xs) ** .5
    return m, s, m - h, m + h

def welch(a, b):   # b - a
    va, vb = st.variance(a) / len(a), st.variance(b) / len(b); d = st.mean(b) - st.mean(a)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)); h = stats.t.ppf(.975, df) * (va + vb) ** .5
    sp = (((len(a) - 1) * st.variance(a) + (len(b) - 1) * st.variance(b)) / (len(a) + len(b) - 2)) ** .5
    g = d / sp * (1 - 3 / (4 * (len(a) + len(b)) - 9)) if sp else float('nan')   # Hedges' g
    return d, d - h, d + h, df, g

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    rows = [run_row(d) for d in sorted(RAW.glob('mixFYF-revD-*-rep[0-9]')) ]
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(OUT / 'runs.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(rows)
    valid = {p: [r for r in rows if r['policy'] == p and r['valid']] for p in POL}
    METRICS = ['total_waf', 'A_waf', 'B_waf', 'C_waf', 'C_first5min_waf', 'C_recovery_s', 'C_detect_s', 'C_explore_windows', 'C_elim', 'C_restored_arms', 'C_learner_ms', 'ycsb_ops', 'B_host']
    st_rows, ct_rows = [], []
    for p in POL:
        n = len(valid[p])
        for k in METRICS:
            xs = [r[k] for r in valid[p] if r.get(k) is not None]
            st_rows.append({'policy': p, 'metric': k, 'n_valid': n, 'values': ' / '.join(f'{x:.4f}' if isinstance(x, float) else str(x) for x in xs),
                            **(dict(zip(['mean', 'sd', 'ci_lo', 'ci_hi'], ci(xs))) if n == 3 and len(xs) == 3 else {'mean': '', 'sd': '', 'ci_lo': '', 'ci_hi': ''})})
    for p in POL[1:]:
        for k in ['C_waf', 'total_waf']:   # pre-registered primary contrasts
            a = [r[k] for r in valid['revD-v4']]; b = [r[k] for r in valid[p]]
            ct_rows.append({'contrast': f'{p} - revD-v4', 'metric': k, **(dict(zip(['diff', 'ci_lo', 'ci_hi', 'welch_df', 'hedges_g'], welch(a, b))) if len(a) == 3 and len(b) == 3 else {'diff': 'n<3: no statistics'})})
    for name, rr in (('stats.csv', st_rows), ('contrasts.csv', ct_rows)):
        with open(OUT / name, 'w', newline='') as f:
            w = csv.DictWriter(f, list(dict.fromkeys(k for r in rr for k in r))); w.writeheader(); w.writerows(rr)
    for r in rows: print(r['policy'], r['rep'], 'valid' if r['valid'] else 'INVALID: ' + r['invalid_reason'], f"C_waf={r.get('C_waf', float('nan')):.4f} total={r.get('total_waf', float('nan')):.4f}")
    for c in ct_rows: print(c)
