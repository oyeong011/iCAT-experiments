#!/usr/bin/env python3
"""revG-20261128 capacity comparison: 8 GiB (GoCom revA-20261114, existing) vs 16 GiB (GoCom revG-20261128, new).

usage: capG_analyze.py [revG raw dir]   (default /home/oy/iCAT/result/revG-20261128/raw; falls back to the report copy)
Reads raw counters only (summary.txt, final-control.txt, device.txt, phase-C-start.time, control-series.txt). Writes
result/revG-20261128-analysis/{runs.csv, stats.csv, capacity_table.csv, capacity_comparison_16g.csv, analysis.md}.
Own derived outputs are regenerated on every call (they are not raw data). Never touches revA raw data.
Validity is taken from checks.tsv (OK lines) plus the same two-path / exit tests; an invalid run is listed, never dropped
silently, and excluded from the statistics with its reason.
"""
import csv, math, re, sys, statistics as st, datetime as dt
from pathlib import Path
from scipy import stats as ss

W = Path('/home/oy/iCAT-final')
G = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/home/oy/iCAT/result/revG-20261128/raw')
if not G.exists(): G = W / 'result/revG-20261128/raw'
A = Path('/home/oy/iCAT/result/revA-20261114/raw')
if not A.exists(): A = W / 'result/revA-20261114/raw'
CHK = G.parent / 'checks.tsv'
OUT = W / 'result/revG-20261128-analysis'; OUT.mkdir(parents=True, exist_ok=True)
GROUPS = [('8 GiB', 'iCAT-v4', A, 'revA-v4', 'revA-20261114'), ('8 GiB', 'Random Selection', A, 'revA-random', 'revA-20261114'),
          ('16 GiB', 'iCAT-v4', G, 'revG-v4', 'revG-20261128'), ('16 GiB', 'Random Selection', G, 'revG-random', 'revG-20261128')]
ok_checks = {}
if CHK.exists():
    for l in CHK.read_text().splitlines():
        f = l.split('\t')
        if len(f) > 2: ok_checks[f[1]] = f[2]


def waf(t, key):
    m = re.search(rf'^{key}[^\n]*? host_pages=(\d+) gc_pages=(\d+)', t, re.M)
    return (int(m[1]), int(m[2]), 1 + int(m[2]) / int(m[1])) if m else (None, None, None)


def c5(d):
    try:
        t0 = dt.datetime.fromisoformat((d / 'phase-C-start.time').read_text().strip()).timestamp()
        ser = [(int(a), int(b), int(c)) for a, b, c in re.findall(r'^(\d+) .*?host_pages=(\d+) gc_pages=(\d+)', (d / 'control-series.txt').read_text(), re.M)]
        s0 = next(s for s in ser if s[0] >= t0); s1 = next(s for s in ser if s[0] >= t0 + 300)
        return 1 + (s1[2] - s0[2]) / (s1[1] - s0[1])
    except Exception: return None


rows = []
for cap, pol, base, grp, batch in GROUPS:
    for d in sorted(base.glob(f'mixFYF-{grp}-rep[0-9]')):
        r = dict(capacity=cap, policy=pol, group=grp, batch=batch, rep=d.name[-1], raw_dir=str(d))
        ec = (d / 'exit-code.txt').read_text().strip() if (d / 'exit-code.txt').exists() else 'missing'
        s = (d / 'summary.txt').read_text() if (d / 'summary.txt').exists() else ''
        h, g, w = waf(s, 'total')
        fc = (d / 'final-control.txt').read_text() if (d / 'final-control.txt').exists() else ''
        parts = re.findall(r'^part=\d host_pages=(\d+) gc_pages=(\d+) gc_count=(\d+)', fc, re.M)
        two = bool(parts) and (sum(int(a) for a, _, _ in parts), sum(int(b) for _, b, _ in parts)) == (h, g)
        sect = int((d / 'device.txt').read_text().split()[1]) if (d / 'device.txt').exists() else None
        r.update(exit=ec, host_pages=h, gc_pages=g, waf_total=w, waf_A=waf(s, 'phaseA')[2], waf_B=waf(s, 'phaseB')[2], waf_C=waf(s, 'phaseC')[2],
                 waf_C_first5min=c5(d), gc_count=sum(int(c) for _, _, c in parts) if parts else None, two_paths_equal=two,
                 logical_bytes=sect * 512 if sect else None, logical_mib=round(sect * 512 / 2**20) if sect else None,
                 host_GiB=h * 4096 / 2**30 if h else None, host_writes_per_capacity=(h * 4096) / (sect * 512) if h and sect else None,
                 check=ok_checks.get(d.name, 'n/a (existing batch, see complete-results/run_validity.csv)' if cap == '8 GiB' else 'missing'))
        r['valid'] = ec == '0' and two and w is not None and (cap == '8 GiB' or r['check'] == 'OK')
        r['reason'] = '' if r['valid'] else ';'.join(x for x, bad in (('exit', ec != '0'), ('two-paths', not two), ('summary', w is None),
                                                                        ('check-run', cap == '16 GiB' and r['check'] != 'OK')) if bad)
        rows.append(r)
F = list(rows[0]) if rows else []
with open(OUT / 'runs.csv', 'w', newline='') as f:
    wr = csv.DictWriter(f, fieldnames=F); wr.writeheader(); wr.writerows(rows)


def desc(xs):
    n = len(xs)
    if n == 0: return dict(n=0)
    m = st.mean(xs)
    if n < 3: return dict(n=n, mean=m, values=' / '.join(f'{x:.5f}' for x in xs), note='n<3: no statistics')
    sd = st.stdev(xs); h = ss.t.ppf(.975, n - 1) * sd / math.sqrt(n)
    return dict(n=n, mean=m, sd=sd, ci_lo=m - h, ci_hi=m + h, values=' / '.join(f'{x:.5f}' for x in xs))


MET = ['waf_total', 'waf_A', 'waf_B', 'waf_C', 'waf_C_first5min', 'host_GiB', 'gc_count', 'host_writes_per_capacity', 'logical_mib']
stats = {}
with open(OUT / 'stats.csv', 'w', newline='') as f:
    wr = csv.writer(f); wr.writerow(['capacity', 'policy', 'metric', 'n', 'values', 'mean', 'sd', 'ci95_lo', 'ci95_hi', 'note'])
    for cap, pol, *_ in GROUPS:
        for m in MET:
            xs = [float(r[m]) for r in rows if r['capacity'] == cap and r['policy'] == pol and r['valid'] and r[m] is not None]
            d = desc(xs); stats[(cap, pol, m)] = d
            wr.writerow([cap, pol, m, d.get('n'), d.get('values', ''), d.get('mean', ''), d.get('sd', ''), d.get('ci_lo', ''), d.get('ci_hi', ''), d.get('note', '')])


def welch(a, b):
    va, vb = st.variance(a) / len(a), st.variance(b) / len(b); se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)); dlt = st.mean(a) - st.mean(b); h = ss.t.ppf(.975, df) * se
    return dlt, dlt - h, dlt + h, df, 2 * ss.t.sf(abs(dlt) / se, df)


f4 = lambda x: '' if x in ('', None) else f'{x:.4f}'
table = []
for cap in ('8 GiB', '16 GiB'):
    rnd = [float(r['waf_total']) for r in rows if r['capacity'] == cap and r['policy'] == 'Random Selection' and r['valid']]
    ic = [float(r['waf_total']) for r in rows if r['capacity'] == cap and r['policy'] == 'iCAT-v4' and r['valid']]
    row = dict(capacity=cap, batch='revA-20261114' if cap == '8 GiB' else 'revG-20261128', n_random=len(rnd), n_icat=len(ic),
               random_mean=st.mean(rnd) if rnd else None, icat_mean=st.mean(ic) if ic else None)
    if len(rnd) >= 3 and len(ic) >= 3:
        dlt, lo, hi, df, p = welch(rnd, ic)
        row.update(delta_random_minus_icat=dlt, welch_lo=lo, welch_hi=hi, welch_df=df, p=p,
                   improvement_pct=(st.mean(rnd) - st.mean(ic)) / st.mean(rnd) * 100, verdict='difference' if lo > 0 or hi < 0 else 'not distinguished')
    else:
        row.update(note='n<3 in a group: no statistics')
    table.append(row)
with open(OUT / 'capacity_table.csv', 'w', newline='') as f:
    keys = ['capacity', 'batch', 'n_random', 'n_icat', 'random_mean', 'icat_mean', 'delta_random_minus_icat', 'welch_lo', 'welch_hi', 'welch_df', 'p', 'improvement_pct', 'verdict', 'note']
    wr = csv.DictWriter(f, fieldnames=keys); wr.writeheader(); wr.writerows(table)

# Excel-ready long table (Capacity_Comparison sheet)
HOSTCFG = 'GoCom (AMD Ryzen 5 3600XT, 32 GiB RAM)'
with open(OUT / 'capacity_comparison_16g.csv', 'w', newline='') as f:
    wr = csv.writer(f)
    wr.writerow(['Policy', 'SSD capacity', 'batch', 'host', 'n', 'rep1', 'rep2', 'rep3', 'mean WAF', 'SD', '95% CI lo', '95% CI hi',
                 'logical capacity MiB', 'host writes GiB (mean)', 'host writes / logical capacity', 'GC count (mean, 4 partitions)', 'WAF phase A', 'WAF phase B', 'WAF phase C'])
    for cap, pol, *_ in GROUPS:
        rs = [r for r in rows if r['capacity'] == cap and r['policy'] == pol and r['valid']]
        d = stats[(cap, pol, 'waf_total')]; v = [f"{float(r['waf_total']):.5f}" for r in rs] + ['', '', '']
        g = lambda m: f4(stats[(cap, pol, m)].get('mean'))
        wr.writerow([pol, cap, 'revA-20261114' if cap == '8 GiB' else 'revG-20261128', HOSTCFG, d.get('n'), *v[:3], f4(d.get('mean')), f4(d.get('sd')), f4(d.get('ci_lo')), f4(d.get('ci_hi')),
                     g('logical_mib'), g('host_GiB'), g('host_writes_per_capacity'), g('gc_count'), g('waf_A'), g('waf_B'), g('waf_C')])
    wr.writerow([])
    for t in table:
        wr.writerow([f"iCAT Improvement (%) vs Random, {t['capacity']}", f4(t.get('improvement_pct')), f"ΔWAF {f4(t.get('delta_random_minus_icat'))} [{f4(t.get('welch_lo'))}, {f4(t.get('welch_hi'))}]", t.get('verdict', t.get('note', ''))])
    wr.writerow(['note', '8 GiB and 16 GiB are different batches (revA 2026-11-14 vs revG, after a reboot with memmap=16G$4G). Same host, same learner code (objdump identical except the block-count constant), same block/page size and OP. GC trigger stays at 2 free lines (fraction halves). The capacity effect is not separable from batch effects; the within-capacity improvement is the primary comparison.'])

inv = [r for r in rows if not r['valid']]
(OUT / 'analysis.md').write_text(f"""# revG-20261128 capacity analysis (auto, {dt.datetime.now().isoformat(timespec='seconds')})

- runs: {len(rows)} (invalid: {len(inv)}{' — ' + '; '.join(r['group'] + ' rep' + r['rep'] + ': ' + r['reason'] for r in inv) if inv else ''})
- files: runs.csv, stats.csv, capacity_table.csv, capacity_comparison_16g.csv
- Improvement (%) = (Random − iCAT) / Random × 100 (point estimate); ΔWAF uses Welch 95 % CI within each capacity (same batch).
""" + '\n'.join(f"- {t['capacity']}: Random {f4(t['random_mean'])} (n={t['n_random']}), iCAT-v4 {f4(t['icat_mean'])} (n={t['n_icat']}), improvement {f4(t.get('improvement_pct'))} %, Δ {f4(t.get('delta_random_minus_icat'))} [{f4(t.get('welch_lo'))}, {f4(t.get('welch_hi'))}]" for t in table) + '\n')
print(open(OUT / 'analysis.md').read())
