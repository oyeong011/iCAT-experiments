#!/usr/bin/env python3
"""Summarize sim/bench logs: per policy x clock mode x seed, per-region ns/call (raw and minus calibrated empty-region cost),
per-GC and per-host-GiB totals. Userspace driver of the real conv_ftl.c, workload=zones 8 GiB x6 (NOT mixY)."""
import re, glob, statistics as st, collections
rows = collections.defaultdict(dict)
for f in sorted(glob.glob('sim/bench/*.log')):
    t = open(f).read(); pol, mode, seed = re.match(r'sim/bench/(.+)-m(\d)-s(\d)\.log', f).groups()
    host = int(re.search(r'invariants=ok', t) and re.search(r'^sim .*host_pages=(\d+)', t, re.M)[1])
    cal = float(re.search(r'empty_region_ns=([\d.]+)', t)[1])
    ru = re.search(r'm1rusage user_s=([\d.]+) sys_s=([\d.]+) maxrss_kb=(\d+)', t)
    reg = collections.defaultdict(lambda: [0, 0])
    for c, n, r, k, ns in [(m[0], 0, m[2], int(m[3]), int(m[4])) for m in re.findall(r'^m1prof clock=(\S+) part=(\d) region=(\S+) calls=(\d+) ns=(\d+)', t, re.M)]:
        reg[r][0] += k; reg[r][1] += ns
    rows[(pol, mode)][seed] = (host, cal, ru, dict(reg))
print('policy\tclock_mode\tregion\tcalls_mean\tns_per_call_raw_mean\tns_per_call_minus_calib_mean\tsd_over_seeds\tns_per_gc_mean\tms_per_host_GiB_mean\tn_seeds')
for (pol, mode), d in sorted(rows.items()):
    for r in ['GC', 'SELECT', 'LEARN', 'REWARD', 'BUF_ABSORB', 'BUF_UNBUF', 'BUF_DRAIN']:
        v = [(x[3][r][0], x[3][r][1], x[1], x[3]['GC'][0], x[0]) for x in d.values() if r in x[3]]
        if not v: continue
        raw = [n / c for c, n, *_ in v]; adj = [n / c - cal for c, n, cal, *_ in v]
        pg = [(n - c * cal) / g for c, n, cal, g, h in v]; pgib = [(n - c * cal) / 1e6 / (h * 4096 / 2**30) for c, n, cal, g, h in v]
        print(f'{pol}\t{mode}\t{r}\t{st.mean(c for c,*_ in v):.0f}\t{st.mean(raw):.1f}\t{st.mean(adj):.1f}\t{st.stdev(adj) if len(adj)>1 else 0:.1f}\t{st.mean(pg):.1f}\t{st.mean(pgib):.2f}\t{len(v)}')
    for k, x in sorted(d.items()):
        print(f'# {pol} mode{mode} seed{k} host_pages={x[0]} calib_ns={x[1]} user_s={x[2][1]} sys_s={x[2][2]} maxrss_kb={x[2][3]}')
