#!/usr/bin/env python3
"""M1 final tables, m1-20261126 (GoCom), user command "M1 SmartGC vs iCAT 자원 오버헤드 실험 완료" (11-26).
Read-only on raw logs; writes NEW files only (refuses to overwrite an existing output directory).
    python3 -I analysis/final_revision/m1_final.py <m1 batch dir> [run-name ...]
      default runs: mixY-m1-icat-v4-rep1 mixY-m1-smartgc-eq8-rep1  (n=1 per policy, user decision 11-26 06:35; 4 runs CANCELLED)
      env M1_OUT=<dir> overrides the output directory (used for the smoke-run dry test).
Outputs: memory_measured.csv, memory_theoretical.csv, memory_comparison.csv, kernel_elapsed_time.csv, userspace_cpu_time.csv,
         common_vs_algorithm_cost.csv, provenance.csv, tables.md
Labels used in every file: measured / calculated (sizeof x allocation formula) / derived (difference of measured values) /
estimated (measured coefficient from another setting) / not measured.
Region nesting (from the patched sources m1-*-src/conv_ftl.c, verified 11-26):
  iCAT    : GC = do_gc  ⊃ SELECT (select_victim_line, CAT score scan) ⊃ -, GC ⊃ LEARN (watgc_v2_on_gc)
  SmartGC : GC = do_gc  ⊃ SELECT (select_victim_line -> smartgc_select) ⊃ LEARN (smartgc_step), GC ⊃ REWARD (smartgc_on_erase)
            BUF_ABSORB / BUF_UNBUF / BUF_DRAIN are on the host write path, outside GC; BUF_DRAIN ⊃ some BUF_UNBUF calls."""
import csv, hashlib, json, os, re, statistics as st, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
C = Path(sys.argv[1]).resolve(); RUNS = sys.argv[2:] or ['mixY-m1-icat-v4-rep1', 'mixY-m1-smartgc-eq8-rep1']
OUT = Path(os.environ.get('M1_OUT') or ROOT / 'result/m1-20261126-final')
if OUT.exists() and any(OUT.iterdir()): sys.exit(f'refusing to overwrite existing {OUT}')
OUT.mkdir(parents=True, exist_ok=True)
REG = ['GC', 'SELECT', 'LEARN', 'REWARD', 'BUF_ABSORB', 'BUF_UNBUF', 'BUF_DRAIN']
pol = lambda r: 'iCAT-v4' if 'icat' in r else 'SmartGC-EQ8'
CALIB_NS = 40.7   # userspace empty-region cost, CLOCK_MONOTONIC, CPU 11 pinned (bench mode 2, mean of 6 seeds 40.5-40.8): ESTIMATE for kernel
REPS = 'n=1 per policy (4 runs CANCELLED by user decision, not failed)'


def wcsv(name, rows):
    with open(OUT / name, 'w', newline='') as f:
        w = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r))); w.writeheader(); w.writerows(rows)


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else 'missing'


# ---------------- provenance ----------------
prov = []
for r in RUNS:
    d = C / 'raw' / r; env = (d / 'environment.txt').read_text(errors='replace')
    ko = re.search(r'([0-9a-f]{64})\s+\S+\.ko', env)
    wl = ';'.join(f'{Path(m[2]).name}={m[1][:16]}' for m in re.finditer(r'([0-9a-f]{64})\s+(\S+)', env)
                  if not m[2].endswith('.ko') and 'runner' not in m[2])
    prov.append(dict(run=r, policy=pol(r), start=env.splitlines()[0], host=env.splitlines()[1].split()[1], kernel=env.splitlines()[1].split()[2],
                     module_sha256=ko[1] if ko else 'missing', runner_sha256=(re.search(r'([0-9a-f]{64})\s+\S+runner-m1.sh', env) or ['', 'missing'])[1],
                     workload='mixY: F S V F V S F S V F V S F S V F V S F S, 20 x 1800 s, 8 GiB NVMeVirt (memmap 8G$4G, cpus=1,2)',
                     workload_files_sha256_16=wl, exit=(d / 'exit-code.txt').read_text().strip(), reps=REPS))
gits = {}
for name, p in (('run_tree_iCAT', '/home/oy/iCAT'), ('analysis_tree_iCAT-final', str(ROOT))):
    try: gits[name] = subprocess.run(['git', '-C', p, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    except Exception: gits[name] = 'unknown'
prov.append(dict(run='GIT_HEAD_AT_ANALYSIS', policy='', start=json.dumps(gits)))
prov.append(dict(run='ANALYSIS_SCRIPT', policy='', start=f'{Path(__file__).relative_to(ROOT)} sha256={sha256(__file__)[:16]}'))
wcsv('provenance.csv', prov)

# ---------------- memory: measured ----------------
mm, mstate = [], {}
for r in RUNS:
    rows = [l.split('\t') for l in (C / 'sampler' / r / 'mem.tsv').read_text().splitlines()[1:]]
    mod = dict(l.split('=', 1) for l in (C / 'sampler' / r / 'module.txt').read_text().split())
    for col, i in (('VmallocUsed', 2), ('Slab', 3), ('SUnreclaim', 4)):
        by = {s: [int(x[i]) for x in rows if x[1] == s] for s in ('pre', 'load1s', 'loaded', 'post')}
        mstate[(r, col)] = by
        base = st.median(by['pre'])
        for s, v in by.items():
            if not v: continue
            mm.append(dict(run=r, policy=pol(r), metric=col, state=s, n_samples=len(v), interval_s=60 if s == 'loaded' else 1,
                           median_kB=st.median(v), min_kB=min(v), max_kB=max(v), sd_kB=round(st.pstdev(v), 1),
                           median_minus_pre_kB=st.median(v) - base, max_minus_pre_kB=max(v) - base,
                           scope='system-wide /proc/meminfo (all kernel allocations, not only nvmev)', kind='measured', unit='kB', reps=REPS))
    mm.append(dict(run=r, policy=pol(r), metric='module coresize', state='load1s', n_samples=1, median_kB=round(int(mod['coresize']) / 1024, 1),
                   scope='/sys/module/nvmev/coresize: module text+data image (included in VmallocUsed)', kind='measured', unit='kB', reps=REPS))
wcsv('memory_measured.csv', mm)

# ---------------- memory: theoretical ----------------
LINES, PGS, P = 8192, 524288, 4
SIZEOF = {'iCAT-v4': dict(line=48, conv_ftl=2960, tuner=2712), 'SmartGC-EQ8': dict(line=72, conv_ftl=3120, tuner=2640, smartgc=232)}
common = [('maptbl', '8 B x tt_pgs(524288) x 4', 8 * PGS * P, 'init: conv_init_ftl vmalloc; free: conv_remove_namespace vfree'),
          ('rmap', '8 B x tt_pgs x 4', 8 * PGS * P, 'same as maptbl')]
TH = {'iCAT-v4': common + [
          ('lines', 'sizeof(struct line)=48 x 8192 x 4', 48 * LINES * P, 'init_lines vmalloc; free at remove'),
          ('conv_ftls', 'sizeof(struct conv_ftl)=2960 x 4 (incl. watgc_v2_tuner 2712 B = iCAT learner state)', 2960 * P, 'namespace init; free at remove')],
      'SmartGC-EQ8': common + [
          ('lines', 'sizeof(struct line)=72 x 8192 x 4', 72 * LINES * P, 'init_lines vmalloc; free at remove'),
          ('conv_ftls', 'sizeof(struct conv_ftl)=3120 x 4 (incl. struct smartgc 232 B; tuner 2640 B present but unused)', 3120 * P, 'namespace init; free at remove'),
          ('Q table', '8 B x 10000 states x 2 actions x 4', 160000 * P, 'smartgc_init vzalloc; vfree in smartgc teardown at remove'),
          ('cand', '32 B x 8192 x 4', 32 * LINES * P, 'smartgc_init'), ('sort_key', '8 B x 8192 x 4', 8 * LINES * P, 'smartgc_init'),
          ('drain list [GC buffer]', '4 B x 8192 x 4', 4 * LINES * P, 'smartgc_init'),
          ('buffered bitmap [GC buffer]', 'tt_pgs/8 B x 4', PGS // 8 * P, 'smartgc_init')]}
mt = []
for p_, items in TH.items():
    for it, formula, b, life in items:
        mt.append(dict(policy=p_, item=it, formula=formula, bytes=b, kB=round(b / 1024, 1), lifetime=life,
                       policy_specific='no' if it in ('maptbl', 'rmap') else 'yes' if it not in ('lines', 'conv_ftls') else 'size differs',
                       kind='calculated (gdb sizeof on the built .ko x allocation formula in conv_ftl.c)'))
    mt.append(dict(policy=p_, item='TOTAL vmalloc by conv_ftl.c', bytes=sum(x[2] for x in items), kB=round(sum(x[2] for x in items) / 1024, 1),
                   kind='calculated'))
wcsv('memory_theoretical.csv', mt)

# ---------------- memory: comparison ----------------
tot = {p_: sum(x[2] for x in items) / 1024 for p_, items in TH.items()}
mc = []
for r in RUNS:
    v = mstate[(r, 'VmallocUsed')]; s = mstate[(r, 'Slab')]; su = mstate[(r, 'SUnreclaim')]
    dv = st.median(v['load1s']) - st.median(v['pre'])
    cs = int(dict(l.split('=', 1) for l in (C / 'sampler' / r / 'module.txt').read_text().split())['coresize']) / 1024
    mc.append(dict(run=r, policy=pol(r), vmalloc_delta_load_kB_measured=dv, theoretical_conv_ftl_vmalloc_kB_calculated=round(tot[pol(r)], 1),
                   module_coresize_kB_measured=round(cs, 1), theoretical_plus_coresize_kB=round(tot[pol(r)] + cs, 1),
                   residual_kB_derived=round(dv - tot[pol(r)] - cs, 1),
                   vmalloc_after_unload_minus_pre_kB_measured=(st.median(v['post']) - st.median(v['pre'])) if v['post'] else '',
                   vmalloc_loaded_max_minus_pre_kB_measured=max(v['loaded']) - st.median(v['pre']) if v['loaded'] else '',
                   slab_delta_load_kB_measured=st.median(s['load1s']) - st.median(s['pre']),
                   sunreclaim_delta_load_kB_measured=st.median(su['load1s']) - st.median(su['pre']),
                   note='Slab/SUnreclaim deltas are system-wide and are not attributed to the policy (both policies share the same slab users)'))
if len(mc) == 2:
    a, b = mc
    mc.append(dict(run='DIFF (SmartGC - iCAT)', policy='',
                   vmalloc_delta_load_kB_measured=b['vmalloc_delta_load_kB_measured'] - a['vmalloc_delta_load_kB_measured'],
                   theoretical_conv_ftl_vmalloc_kB_calculated=round(tot['SmartGC-EQ8'] - tot['iCAT-v4'], 1),
                   module_coresize_kB_measured=round(b['module_coresize_kB_measured'] - a['module_coresize_kB_measured'], 1),
                   slab_delta_load_kB_measured=b['slab_delta_load_kB_measured'] - a['slab_delta_load_kB_measured'],
                   sunreclaim_delta_load_kB_measured=b['sunreclaim_delta_load_kB_measured'] - a['sunreclaim_delta_load_kB_measured'],
                   note='n=1 each: single difference, no test. Measured window identical (sampler.sh states pre/load1s/loaded/post).'))
wcsv('memory_comparison.csv', mc)

# ---------------- kernel elapsed time ----------------
ke, kd, info = [], {}, {}
for r in RUNS:
    k = (C / 'raw' / r / 'kernel.log').read_text(errors='replace')   # kernel.log only (kernel-final.log may hold a previous run's lines)
    lines = re.findall(r'M1PROF when=stop clock=(\S+) part=(\d) region=(\S+) calls=(\d+) ns=(\d+) max_ns=(\d+)', k)
    assert sum(1 for x in lines if x[2] == 'GC') == 4, f'{r}: need exactly one stop set'
    fc = (C / 'raw' / r / 'final-control.txt').read_text()
    host = int(re.search(r'host_pages=(\d+)', fc.splitlines()[0])[1]); gib = host * 4096 / 2**30
    info[r] = dict(host_GiB=gib)
    agg = {}
    for clock, p, reg, calls, ns, mx in lines:
        a = agg.setdefault(reg, dict(calls=0, ns=0, mx=0, per=[])); a['calls'] += int(calls); a['ns'] += int(ns); a['mx'] = max(a['mx'], int(mx))
        a['per'].append(int(ns) / int(calls)); a['clock'] = clock
    gc_calls = agg['GC']['calls']; kd[r] = agg
    for reg in REG:
        if reg not in agg: continue
        a = agg[reg]
        ke.append(dict(run=r, policy=pol(r), region=reg, clock=a['clock'] + ' (kernel ktime_get_ns ELAPSED time, not CPU time)', partitions=len(a['per']),
                       calls=a['calls'], total_ns=a['ns'], total_s=round(a['ns'] / 1e9, 3), mean_ns_per_call=round(a['ns'] / a['calls'], 1),
                       partition_mean_min_ns=round(min(a['per']), 1), partition_mean_max_ns=round(max(a['per']), 1),
                       partition_mean_sd_ns=round(st.stdev(a['per']), 1), max_single_call_ns=a['mx'],
                       ns_per_gc=round(a['ns'] / gc_calls, 1), ms_per_host_GiB=round(a['ns'] / 1e6 / gib, 3),
                       p50_p95_p99='not available: only calls / sum / max are kept per partition (no per-call samples)',
                       timer_overhead_est_ns_per_call=CALIB_NS, timer_overhead_label='estimated (userspace calibration, not measured in kernel)',
                       unit='ns, s, ms', kind='measured', reps=REPS))
wcsv('kernel_elapsed_time.csv', ke)

# ---------------- independent cross-check of the M1PROF counters ----------------
# (a) when=stop vs when=remove (same counters printed twice; remove comes after the run) in kernel-final.log,
# (b) M1PROF GC calls per partition vs gc_count in final-control.txt (FTL counter, independent of the timer code).
xc = []
for r in RUNS:
    d = C / 'raw' / r
    kf = (d / 'kernel-final.log').read_text(errors='replace')
    pat = r'M1PROF when={} clock=\S+ part=(\d) region=(\S+) calls=(\d+) ns=(\d+) max_ns=(\d+)'
    stop = {(p, g): (c, n) for p, g, c, n, _ in re.findall(pat.format('stop'), (d / 'kernel.log').read_text(errors='replace'))}
    rem = {(p, g): (c, n) for p, g, c, n, _ in re.findall(pat.format('remove'), kf)}
    fcp = {int(p): int(c) for p, c in re.findall(r'^part=(\d) .*?gc_count=(\d+)', (d / 'final-control.txt').read_text(), re.M)}
    for (p, g), (c, n) in sorted(stop.items()):
        rc = rem.get((p, g))
        xc.append(dict(run=r, policy=pol(r), part=p, region=g, stop_calls=c, remove_calls=rc[0] if rc else 'missing', stop_equals_remove=bool(rc) and rc == (c, n),
                       final_control_gc_count=fcp.get(int(p), '') if g == 'GC' else '', gc_calls_equal_gc_count=(int(c) == fcp.get(int(p))) if g == 'GC' else ''))
wcsv('crosscheck_m1prof.csv', xc)

# ---------------- WAF and run integrity (n=1 each: single values, no CI / test) ----------------
wi = []
for r in RUNS:
    d = C / 'raw' / r; fc = (d / 'final-control.txt').read_text()
    h, g = map(int, re.search(r'host_pages=(\d+) gc_pages=(\d+)', fc.splitlines()[0]).groups())
    parts = re.findall(r'^part=\d host_pages=(\d+) gc_pages=(\d+) gc_count=(\d+)', fc, re.M)
    sg = re.findall(r'^smartgc part=\d .*?absorbed=(\d+) evicted=(\d+).*?nand_pages=(\d+)', fc, re.M)
    klog = (d / 'kernel.log').read_text(errors='replace')
    fio_err = sum(1 for j in d.glob('phase-S*.json') if any(x['error'] for x in json.loads(j.read_text())['jobs']))
    fb = list(d.glob('filebench-S*.txt'))
    wi.append(dict(run=r, policy=pol(r), exit=(d / 'exit-code.txt').read_text().strip(), host_pages=h, gc_pages=g, host_TB=round(h * 4096 / 1e12, 3),
                   waf_two_paths_equal=(h, g) == (sum(int(x[0]) for x in parts), sum(int(x[1]) for x in parts)),
                   waf_1_plus_gc_over_host=round(1 + g / h, 6),
                   absorbed=sum(int(x[0]) for x in sg) if sg else '', evicted=sum(int(x[1]) for x in sg) if sg else '',
                   nand_pages=sum(int(x[2]) for x in sg) if sg else '',
                   waf_nand=round(sum(int(x[2]) for x in sg) / h, 6) if sg else round(1 + g / h, 6),
                   gc_count=sum(int(x[2]) for x in parts), fio_phases=len(list(d.glob('phase-S*.json'))), fio_phases_with_error=fio_err,
                   filebench_phases=len(fb), filebench_io_summary_ok=sum('IO Summary' in f.read_text(errors='replace') for f in fb),
                   kernel_errors=len(re.findall(r'BUG[: ]|Oops|Call Trace|soft lockup|hung_task|blocked for more than', klog)),
                   chmodel_warn_lines=klog.count('Need to increase array size'), ycsb='not applicable (mixY has no YCSB / SQLite phase)',
                   note='n=1: single value, no CI or significance test'))
wcsv('waf_and_integrity.csv', wi)

# ---------------- userspace CPU time (separate table; NOT compared 1:1 with kernel ktime) ----------------
us = []
bs = C / 'analysis' / 'bench_summary.tsv'
for l in bs.read_text().splitlines():
    if l.startswith('policy') or not l.strip(): continue
    if l.startswith('#'):
        m = re.match(r'# (\S+) mode(\d) seed(\d) host_pages=(\d+) calib_ns=(\S+) user_s=(\S+) sys_s=(\S+) maxrss_kb=(\d+)', l)
        if m: us.append(dict(policy=m[1], clock_mode=m[2], clock='process getrusage', region='WHOLE PROCESS', seed=m[3], user_s=m[6], sys_s=m[7],
                             calib_ns=m[5], sim_process_maxrss_kB=m[8],
                             note='maxrss = userspace simulator process RSS, NOT the kernel module memory', kind='measured'))
        continue
    pl, mode, reg, calls, raw, net, sd, pergc, msg, n = l.split('\t')
    us.append(dict(policy=pl, clock_mode=mode, clock='CLOCK_THREAD_CPUTIME_ID (thread CPU time)' if mode == '1' else 'CLOCK_MONOTONIC pinned CPU 11 (elapsed, no I/O/wait)',
                   region=reg, seed='mean of ' + n, calls=calls, ns_per_call_raw=raw, ns_per_call_minus_calib=net, sd_over_seeds=sd, ns_per_gc=pergc,
                   ms_per_host_GiB=msg, workload='sim zones 60/30/10 %, 8 GiB x 6 overwrites, 4 partitions (NOT mixY)',
                   validity='mode 1 valid for long regions only (~0.86 us clock read inflates nested/short regions; negative values = below resolution)'
                   if mode == '1' else 'mode 2 is elapsed time on an idle pinned core; used as a CPU-time proxy only, labelled as such',
                   kind='measured', reps='3 seeds per policy x mode'))
wcsv('userspace_cpu_time.csv', us)

# ---------------- common vs algorithm cost ----------------
cv = []
for r in RUNS:
    a, gib, p_ = kd[r], info[r]['host_GiB'], pol(r)
    g = lambda x: a.get(x, {}).get('ns', 0)
    calls = a['GC']['calls']

    def row(cat, ns, how, kind, note=''):
        cv.append(dict(run=r, policy=p_, category=cat, total_s=round(ns / 1e9, 3) if ns is not None else '', ms_per_host_GiB=round(ns / 1e6 / gib, 3) if ns is not None else '',
                       ns_per_gc=round(ns / calls, 1) if ns is not None else '', derivation=how, kind=kind, note=note, clock='ktime elapsed (not CPU time)'))
    row('NVMeVirt common processing (I/O dispatch, NAND timing model, DMA copy)', None, 'not instrumented', 'not measured',
        'dispatcher kthreads busy-poll CPU 1-2 at ~100 % for every policy; /proc/stat cannot separate it')
    row('FTL common write/read path (mapping update, line allocation)', None, 'not instrumented', 'not measured')
    if p_ == 'iCAT-v4':
        row('GC common work (page copy, erase, bookkeeping)', g('GC') - g('SELECT') - g('LEARN'), 'GC - SELECT - LEARN', 'derived',
            'includes nested timer overhead (~2 regions) and depends on victim valid pages, which differs between policies')
        row('victim selection (policy)', g('SELECT'), 'SELECT (CAT score scan over all lines)', 'measured')
        row('iCAT learning / score update', g('LEARN'), 'LEARN = watgc_v2_on_gc', 'measured')
    else:
        row('GC common work (page copy, erase, bookkeeping)', g('GC') - g('SELECT') - g('REWARD'), 'GC - SELECT - REWARD', 'derived',
            'includes nested timer overhead (~3 regions) and depends on victim valid pages, which differs between policies')
        row('victim selection (policy, excluding learning step)', g('SELECT') - g('LEARN'), 'SELECT - LEARN', 'derived')
        row('SmartGC learning step (Q update, state scoring, candidate sort)', g('LEARN'), 'LEARN = smartgc_step', 'measured')
        row('SmartGC reward (on erase)', g('REWARD'), 'REWARD = smartgc_on_erase', 'measured')
        row('SmartGC GC buffer on write path (absorb + unbuffer + drain)', g('BUF_ABSORB') + g('BUF_UNBUF') + g('BUF_DRAIN'),
            'BUF_ABSORB + BUF_UNBUF + BUF_DRAIN (drain contains part of the unbuffer calls: upper bound, double count possible)', 'measured (upper bound)',
            'outside do_gc; policy-specific cost on the host write path')
wcsv('common_vs_algorithm_cost.csv', cv)

# ---------------- tables.md (numbers only; judgments are written by hand in m1_final_report.md) ----------------
md = ['# m1-20261126 final tables (generated by m1_final.py; ' + REPS + ')', '', '## kernel elapsed time (ktime, NOT CPU time)', '',
      '| policy | region | calls | total s | mean ns/call | partition mean min-max | max ns | ms/host GiB |', '|---|---|---|---|---|---|---|---|']
md += [f"| {x['policy']} | {x['region']} | {x['calls']:,} | {x['total_s']:,} | {x['mean_ns_per_call']:,} | {x['partition_mean_min_ns']:,}-{x['partition_mean_max_ns']:,} | {x['max_single_call_ns']:,} | {x['ms_per_host_GiB']} |" for x in ke]
md += ['', '## common vs algorithm (ktime elapsed)', '', '| policy | category | total s | ms/host GiB | ns/GC | kind |', '|---|---|---|---|---|---|']
md += [f"| {x['policy']} | {x['category']} | {x['total_s']} | {x['ms_per_host_GiB']} | {x['ns_per_gc']} | {x['kind']} |" for x in cv]
md += ['', '## memory', '', '| run | VmallocUsed Δ load (meas.) | conv_ftl.c vmalloc (calc.) | coresize (meas.) | residual | after unload | Slab Δ | SUnreclaim Δ |', '|---|---|---|---|---|---|---|---|']
md += [f"| {x['run']} | {x.get('vmalloc_delta_load_kB_measured')} | {x.get('theoretical_conv_ftl_vmalloc_kB_calculated')} | {x.get('module_coresize_kB_measured')} | {x.get('residual_kB_derived', '')} | {x.get('vmalloc_after_unload_minus_pre_kB_measured', '')} | {x.get('slab_delta_load_kB_measured')} | {x.get('sunreclaim_delta_load_kB_measured')} |" for x in mc]
(OUT / 'tables.md').write_text('\n'.join(md) + '\n')
print('wrote', OUT); print('\n'.join(md))
