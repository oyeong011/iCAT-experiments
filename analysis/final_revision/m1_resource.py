#!/usr/bin/env python3
"""M1 resource comparison, m1-20261126 (GoCom). Read-only on raw logs; writes NEW files only.
    python3 -I analysis/final_revision/m1_resource.py <m1 batch dir> [run-name ...]
      default runs: mixY-m1-icat-v4-rep1 mixY-m1-smartgc-eq8-rep1   (n=1 per policy, user decision 11-26 06:35)
Outputs -> result/m1-20261126-analysis/ : conditions.csv, regions.csv, regions_partition.csv, memory.csv, memory_expected.csv,
           waf.csv, report.md
Definitions / limits (also printed in report.md):
  * region timers are kernel ktime_get_ns() ELAPSED time around a function call (not CPU time). Each run gives calls, total ns and
    max ns per partition and region (M1PROF when=stop). No per-call samples were kept -> p50/p95/p99 and within-run variance are NOT
    available; between-partition spread of the per-call mean (4 partitions) is reported instead.
  * timer overhead (two clock reads + counter update per call) was not measured in the kernel; the userspace calibration (empty region
    with CLOCK_MONOTONIC, same code) is quoted as an ESTIMATE, labelled as such.
  * memory: /proc/meminfo VmallocUsed (pages allocated through vmalloc, incl. the module image) median of 60 x 1 s samples before load
    vs median of the 60 x 1 s samples after load, and the post-unload return. Compared with sizes computed from DWARF (gdb sizeof)."""
import csv, json, re, statistics as st, sys, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
C = Path(sys.argv[1]); RUNS = sys.argv[2:] or ['mixY-m1-icat-v4-rep1', 'mixY-m1-smartgc-eq8-rep1']
OUT = ROOT / ('result/m1-20261126-analysis' + ('-smoke-test' if any('smoke' in r for r in RUNS) else '')); OUT.mkdir(parents=True, exist_ok=True)
REG = ['GC', 'SELECT', 'LEARN', 'REWARD', 'BUF_ABSORB', 'BUF_UNBUF', 'BUF_DRAIN']
pol = lambda r: 'iCAT-v4' if 'icat' in r else 'SmartGC-EQ8'


def wcsv(name, rows):
    with open(OUT / name, 'w', newline='') as f:
        w = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r))); w.writeheader(); w.writerows(rows)


# ---- 1. conditions ----
def cond(d):
    rd = lambda p: (d / p).read_text(errors='replace') if (d / p).exists() else ''
    env = rd('environment.txt').splitlines()
    c = {'host': env[1].split()[1] if len(env) > 1 else '', 'kernel': env[1].split()[2] if len(env) > 1 else '',
         'cmdline_memmap': (re.search(r'memmap=\S+', env[2]) or [''])[0] if len(env) > 2 else '',
         'fio': env[3] if len(env) > 3 else ''}
    for l in env:
        m = re.match(r'([0-9a-f]{64})\s+(\S+)', l)
        if m and not m[2].endswith('.ko') and 'runner' not in m[2]: c['sha:' + Path(m[2]).name] = m[1][:16]
        if m and m[2].endswith('.ko'): c['module_sha'] = m[1][:16]
    c['varmail.f_md5'] = hashlib.md5(rd('varmail.f').encode()).hexdigest()[:16]
    for f in ('preset.json', 'prepare.json'):
        try: c[f] = json.dumps([x['job options'] for x in json.loads(rd(f))['jobs']], sort_keys=True)
        except Exception: c[f] = 'missing'
    ph = sorted(d.glob('phase-S*.json'))
    c['fio_phases'] = len(ph); c['filebench_phases'] = len(list(d.glob('filebench-S*.txt')))
    c['fio_job_options_hash'] = hashlib.md5(''.join(json.dumps([x['job options'] for x in json.loads(p.read_text())['jobs']], sort_keys=True)
                                                    for p in ph).encode()).hexdigest()[:16]
    seq = [('F' if (d / f'phase-S{i:02d}.json').exists() else 'V' if (d / f'filebench-S{i:02d}.txt').exists() else '?') for i in range(1, 21)]
    c['phase_kinds'] = ''.join(seq).rstrip('?')
    k = rd('kernel.log')
    c['insmod_args'] = ' '.join(sorted(set(re.findall(r'(?:icat_seed|smartgc_seed|cpus|memmap_start|memmap_size)=\S+', rd('console.txt') + k))))
    c['mkfs_blocks'] = (re.search(r'Block count:\s+(\d+)', rd('mkfs.txt')) or re.search(r'(\d+) blocks', rd('mkfs.txt')) or [''])[0]
    c['exit'] = rd('exit-code.txt').strip()
    return c


conds = []
for r in RUNS:
    conds.append({'run': r, 'policy': pol(r), **cond(C / 'raw' / r)})
same = {k: len({c.get(k) for c in conds}) == 1 for k in conds[0] if k not in ('run', 'policy', 'module_sha', 'insmod_args', 'exit')}
wcsv('conditions.csv', conds + [{'run': 'SAME_ACROSS_RUNS', **{k: v for k, v in same.items()}}])

# ---- 2-4. region timers ----
rows, prow = [], []
for r in RUNS:
    # kernel.log only: the runner cuts it at this run's BEGIN marker. kernel-final.log is the whole dmesg ring and still holds the
    # previous run's M1PROF lines (found 11-26 on the smokes), so it must NOT be used for per-run values.
    k = (C / 'raw' / r / 'kernel.log').read_text(errors='replace')
    n_stop_gc = len(re.findall(r'M1PROF when=stop \S+ part=\d region=GC ', k))
    assert n_stop_gc == 4, f'{r}: expected one M1PROF stop set (4 GC lines) in kernel.log, found {n_stop_gc}'
    pr = {}
    for clock, p, reg, calls, ns, mx in re.findall(r'M1PROF when=stop clock=(\S+) part=(\d) region=(\S+) calls=(\d+) ns=(\d+) max_ns=(\d+)', k):
        pr[(int(p), reg)] = (clock, int(calls), int(ns), int(mx))
    fc = (C / 'raw' / r / 'final-control.txt').read_text()
    host = int(re.search(r'host_pages=(\d+)', fc.splitlines()[0])[1]); gcn = sum(int(x) for x in re.findall(r'^part=\d .*?gc_count=(\d+)', fc, re.M))
    gc_calls = sum(v[1] for (p, g), v in pr.items() if g == 'GC')
    for reg in REG:
        ps = [(p, *pr[(p, reg)]) for p in range(4) if (p, reg) in pr]
        if not ps: continue
        for p, clock, calls, ns, mx in ps:
            prow.append(dict(run=r, policy=pol(r), part=p, region=reg, clock=clock, calls=calls, total_ns=ns, ns_per_call=round(ns / calls, 1), max_ns=mx))
        calls = sum(x[2] for x in ps); ns = sum(x[3] for x in ps); per = [x[3] / x[2] for x in ps]
        rows.append(dict(run=r, policy=pol(r), region=reg, clock=ps[0][1], partitions=len(ps), calls=calls, total_ns=ns, total_s=round(ns / 1e9, 3),
                         ns_per_call=round(ns / calls, 1), part_mean_min=round(min(per), 1), part_mean_max=round(max(per), 1),
                         part_mean_sd=round(st.stdev(per), 1) if len(per) > 1 else '', max_ns=max(x[4] for x in ps),
                         ns_per_gc=round(ns / gc_calls, 1) if gc_calls else '', ms_per_host_GiB=round(ns / 1e6 / (host * 4096 / 2**30), 3),
                         gc_count_final_control=gcn, host_pages=host, p50_p95_p99='not available (no per-call samples kept)'))
wcsv('regions.csv', rows); wcsv('regions_partition.csv', prow)

# ---- 5. memory ----
mem, exp = [], []
for r in RUNS:
    t = [l.split('\t') for l in (C / 'sampler' / r / 'mem.tsv').read_text().splitlines()[1:]]
    g = lambda s, i=2: [int(x[i]) for x in t if x[1] == s]
    mod = dict(l.split('=', 1) for l in (C / 'sampler' / r / 'module.txt').read_text().split())
    pre, l1, lo, post = g('pre'), g('load1s'), g('loaded'), g('post')
    mem.append(dict(run=r, policy=pol(r), n_pre=len(pre), vmalloc_pre_median_kb=st.median(pre), n_load1s=len(l1), vmalloc_load1s_median_kb=st.median(l1),
                    delta_load_kb=st.median(l1) - st.median(pre), vmalloc_loaded_min_kb=min(lo) if lo else '', vmalloc_loaded_max_kb=max(lo) if lo else '',
                    vmalloc_post_median_kb=st.median(post) if post else '', delta_after_unload_kb=(st.median(post) - st.median(pre)) if post else '',
                    pre_sd_kb=round(st.pstdev(pre), 1), slab_delta_kb=st.median(g('load1s', 3)) - st.median(g('pre', 3)),
                    module_coresize_B=mod.get('coresize'), kind='measured (VmallocUsed, /proc/meminfo, kB)'))
wcsv('memory.csv', mem)
# expected vmalloc from DWARF sizes (gdb sizeof on the two .ko files) and the allocation sites in conv_ftl.c
LINES, PGS, P = 8192, 524288, 4
common = {'maptbl (8 B x tt_pgs)': 8 * PGS * P, 'rmap (8 B x tt_pgs)': 8 * PGS * P}
E = {'iCAT-v4': {**common, 'lines (48 B x 8192)': 48 * LINES * P, 'conv_ftls (2960 B, incl. watgc_v2_tuner 2712 B)': 2960 * P},
     'SmartGC-EQ8': {**common, 'lines (72 B x 8192)': 72 * LINES * P, 'conv_ftls (3120 B, incl. struct smartgc 232 B, tuner 2640 B unused)': 3120 * P,
                     'Q table (8 B x 10000 states x 2)': 160000 * P, 'cand (32 B x 8192)': 32 * LINES * P, 'sort_key (8 B x 8192)': 8 * LINES * P,
                     'drain (4 B x 8192) [GC buffer]': 4 * LINES * P, 'buffered bitmap (tt_pgs/8) [GC buffer]': PGS // 8 * P}}
for p_, d in E.items():
    for k_, v in d.items(): exp.append(dict(policy=p_, item=k_, bytes=v, kind='calculated (gdb sizeof x allocation formula), 4 partitions'))
    exp.append(dict(policy=p_, item='TOTAL vmalloc by conv_ftl.c', bytes=sum(d.values()), kind='calculated'))
wcsv('memory_expected.csv', exp)

# ---- WAF (single values, n=1: no test) ----
waf = []
for r in RUNS:
    line = [l for l in open(C / 'checks.tsv') if l.startswith(r + '\t')]
    m = dict(x.split('=', 1) for x in line[-1].split('\t')[2].split()) if line else {}
    waf.append(dict(run=r, policy=pol(r), check=line[-1].split('\t')[1] if line else 'missing', waf=m.get('waf'), waf_nand=m.get('waf_nand'),
                    gc_count=m.get('gc_count'), fio_jobs_below_95pct=m.get('fio_jobs_below_95pct_of_target'), chmodel_warn_lines=m.get('chmodel_warn_lines'),
                    note='n=1: single value, no CI / significance test'))
wcsv('waf.csv', waf)
print('wrote', OUT)
for x in rows: print(x['policy'], x['region'], x['calls'], x['total_s'], x['ns_per_call'], x['part_mean_min'], x['part_mean_max'], x['ns_per_gc'], x['ms_per_host_GiB'])
for x in mem: print(x)
print({k: v for k, v in same.items() if not v})
