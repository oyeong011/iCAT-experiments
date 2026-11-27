#!/usr/bin/env python3
"""11-27 independent M1 resource re-computation from raw kernel logs / samplers (no 고컴/승컴 analysis code imported).
    python3 -I -B analysis/revision/m1_validation.py GOCOM_DIR
GOCOM_DIR holds result/{revA-20261114,m1-20261126,m1-20261126-final,m1-20261126-analysis}
          (origin/report/data-validity-20261124) and result/resource-v124-20261114 (origin/resource-overhead-20261114).
Every timing here is kernel ktime_get_ns ELAPSED time. None of it is labelled CPU time.
Outputs result/final-validation-20261127/m1_recalc.csv (one row per source x run x item, with the pushed value and the diff)."""
import csv, gzip, re, statistics as st, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'result/final-validation-20261127'
G = Path(sys.argv[1]) / 'result'
rows = []

def add(src, run, item, kind, val, pushed='', pushed_where=''):
    d = (abs(val - float(pushed)) if pushed not in ('', None) and val not in ('', None) else '')
    rows.append({'source': src, 'run': run, 'item': item, 'kind': kind, 'recalc': val, 'pushed': pushed, 'pushed_where': pushed_where,
                 'abs_diff': d, 'agree': (d == '' or d <= tol(pushed))})

def tol(p):   # half a unit of the pushed value's last printed decimal (pushed tables round), floor 1e-9
    s = str(p); return max(1e-9, 0.5 * 10 ** -(len(s.split('.')[1]) if '.' in s else 0)) if len(s.split('.')[-1]) < 6 else 1e-6 * max(1, abs(float(p)))

# 1. 승컴 resource-v124 (mixY S01 FIO-Fast 1800 s, i7-7700): RESOURCE slot lines, 4 partitions summed
RV = G / 'resource-v124-20261114'
POL = {'resfixed47': 'Fixed CAT-47', 'resv1': 'iCAT v1', 'resv2': 'iCAT v2', 'resv4': 'iCAT v4'}
summ = {(r['policy'], r['metric']): r for r in csv.DictReader(open(RV / 'report/cpu_overhead_summary.csv'))}
per = {}
for d in sorted(RV.glob('mixY-res*-rep[123]')):
    p = POL.get(re.match(r'mixY-(res\w+?)-rep', d.name)[1])
    if not p: continue
    s = {}
    for m in re.finditer(r'RESOURCE part=\d slot=(\w+) n=(\d+) sum_ns=(\d+)', (d / 'kernel.log').read_text(errors='replace')):
        a = s.setdefault(m[1], [0, 0]); a[0] += int(m[2]); a[1] += int(m[3])
    alg = (s['observe'][1] + s['setarm'][1]) / 1e6
    per.setdefault(p, []).append({'alg_ms': alg, 'ongc_ms': s['ongc'][1] / 1e6, 'ongc_per_gc_ns': s['ongc'][1] / s['ongc'][0],
                                  'gc_calls': s['dogc'][0], 'gc_minus_ongc_ms': (s['dogc'][1] - s['ongc'][1]) / 1e6})
    add('승컴 resource-v124', d.name, 'algorithm (observe+set_arm) ms', 'ktime elapsed', alg)
    sm = [l for l in (d.parent / f'{d.name[5:]}.samples.txt').read_text().splitlines()] if (d.parent / f'{d.name[5:]}.samples.txt').exists() else []
    v = lambda tag: [int(re.search(r'VmallocUsed=(\d+)', l)[1]) for l in sm if f'tag={tag}' in l]
    if v('before') and v('loaded'): add('승컴 resource-v124', d.name, 'VmallocUsed loaded - before kB', 'measured /proc/meminfo', v('loaded')[0] - v('before')[-1])
for p, xs in per.items():
    for k, metric in (('alg_ms', '알고리즘 CPU (observe + set_arm, 4파티션) [ms]'), ('ongc_ms', 'on_gc 전체 (타이머 비용 포함, 상한) [ms]'),
                      ('ongc_per_gc_ns', 'GC당 on_gc (타이머 포함) [ns]'), ('gc_calls', 'GC 횟수 (do_gc 호출)')):
        add('승컴 resource-v124', f'{p} mean n={len(xs)}', metric, 'ktime elapsed (pushed label says CPU)' if 'CPU' in metric else 'ktime elapsed / count',
            st.mean(x[k] for x in xs), summ.get((p, metric), {}).get('mean', ''), 'origin/resource-overhead-20261114:result/resource-v124-20261114/report/cpu_overhead_summary.csv')

# 2. 고컴 revA learner_ns (mixFYF 90 min): sum of learner_ns over WATGC_V2 sample lines
cm = {r['run']: r for r in csv.DictReader(open(G / 'revA-20261114/results/resource/cpu_measurements.csv'))}
for d in sorted((G / 'revA-20261114/raw').glob('mixFYF-*-rep[123]')):
    kl = (d / 'kernel.log').read_text(errors='replace')
    last, n = {}, 0   # learner_ns is CUMULATIVE per partition -> total = sum of each partition's last value
    for m in re.finditer(r'WATGC_V2 sample .*part=(\d) .*learner_ns=(\d+)', kl): last[m[1]] = int(m[2]); n += 1
    add('고컴 revA', d.name, 'learner_ns total ms', 'ktime elapsed (learner_ns), NOT CPU time', sum(last.values()) / 1e6,
        cm.get(d.name, {}).get('learner_total_ms', ''), f'origin/report/data-validity-20261124:result/revA-20261114/results/resource/cpu_measurements.csv')
    add('고컴 revA', d.name, 'learner decisions (sample lines with learner_ns)', 'count', n, cm.get(d.name, {}).get('learner_calls', ''), 'same')

# 3. 고컴 m1 (mixY 10 h, n=1 per policy): M1PROF when=stop, sampler mem.tsv / stat.tsv
ke = {(r['run'], r['region']): r for r in csv.DictReader(open(G / 'm1-20261126-final/kernel_elapsed_time.csv'))}
me = {r['run']: r for r in csv.DictReader(open(G / 'm1-20261126-analysis/memory.csv'))}
KF = 'origin/report/data-validity-20261124:result/m1-20261126-final/kernel_elapsed_time.csv'
for run in ('mixY-m1-icat-v4-rep1', 'mixY-m1-smartgc-eq8-rep1'):
    kl = gzip.open(G / f'm1-20261126/raw/{run}/kernel.log.gz', 'rt', errors='replace').read()
    agg, part = {}, {}
    for m in re.finditer(r'M1PROF when=stop clock=ktime_elapsed part=(\d) region=(\w+) calls=(\d+) ns=(\d+) max_ns=(\d+)', kl):
        a = agg.setdefault(m[2], [0, 0]); a[0] += int(m[3]); a[1] += int(m[4])
        part.setdefault(m[2], []).append((int(m[4]) / int(m[3]) if int(m[3]) else 0, int(m[5])))
    host = int(re.search(r'host_pages=(\d+)', (G / f'm1-20261126/raw/{run}/stopped.txt').read_text())[1])
    gcn = agg['GC'][0]
    for reg, (c, ns) in agg.items():
        add('고컴 m1', run, f'{reg} ns per GC', 'ktime elapsed, NOT CPU time', ns / gcn, ke.get((run, reg), {}).get('ns_per_gc', ''), KF)
        add('고컴 m1', run, f'{reg} us per call', 'ktime elapsed, NOT CPU time', ns / c / 1e3)
    for reg, ps in part.items():
        k = ke.get((run, reg), {})
        add('고컴 m1', run, f'{reg} partition mean min ns', 'ktime elapsed, NOT CPU time', min(x for x, _ in ps), k.get('partition_mean_min_ns', ''), KF)
        add('고컴 m1', run, f'{reg} partition mean max ns', 'ktime elapsed, NOT CPU time', max(x for x, _ in ps), k.get('partition_mean_max_ns', ''), KF)
        add('고컴 m1', run, f'{reg} max single call ns', 'ktime elapsed, NOT CPU time', max(y for _, y in ps), k.get('max_single_call_ns', ''), KF)
        add('고컴 m1', run, f'{reg} ms per host GiB', 'ktime elapsed, NOT CPU time', agg[reg][1] / 1e6 / (host * 4096 / 2 ** 30), k.get('ms_per_host_GiB', ''), KF)
    for reg, (c, ns) in agg.items():
        k = ke.get((run, reg), {})
        add('고컴 m1', run, f'{reg} calls', 'count', c, k.get('calls', ''), KF)
        add('고컴 m1', run, f'{reg} total s', 'ktime elapsed, NOT CPU time', ns / 1e9, k.get('total_s', ''), KF)
        add('고컴 m1', run, f'{reg} ns/call', 'ktime elapsed, NOT CPU time', ns / c, k.get('mean_ns_per_call', ''), KF)
    mt = list(csv.DictReader(open(G / f'm1-20261126/sampler/{run}/mem.tsv'), delimiter='\t'))
    med = lambda s: st.median(int(r['vmalloc_used_kb']) for r in mt if r['state'] == s)
    add('고컴 m1', run, 'VmallocUsed load1s median - pre median kB', 'measured /proc/meminfo', med('load1s') - med('pre'),
        me[run]['delta_load_kb'], 'origin/report/data-validity-20261124:result/m1-20261126-analysis/memory.csv')
    add('고컴 m1', run, 'VmallocUsed post median - pre median kB', 'measured /proc/meminfo', med('post') - med('pre'), me[run]['delta_after_unload_kb'], 'same')
    add('고컴 m1', run, 'VmallocUsed loaded median - pre median kB', 'measured /proc/meminfo', med('loaded') - med('pre'))
    st_ = [l.split('\t') for l in open(G / f'm1-20261126/sampler/{run}/stat.tsv')]
    for cpu in ('cpu1', 'cpu2'):
        f = lambda l: next(list(map(int, x.split()[1:])) for x in l[1].split('|') if x.startswith(cpu + ' '))
        a, b = f(st_[0]), f(st_[-1]); tot = sum(b) - sum(a); idle = (b[3] + b[4]) - (a[3] + a[4])
        add('고컴 m1', run, f'{cpu} busy % (/proc/stat, whole run)', 'measured, but busy-poll saturates it', 100 * (tot - idle) / tot)

with open(OUT / 'm1_recalc.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
print(f'{len(rows)} rows, compared={sum(r["pushed"] != "" for r in rows)}, disagree={sum(not r["agree"] for r in rows)}')
for r in rows:
    if not r['agree'] or 'mean' in r['run'] or 'busy' in r['item'] or 'Vmalloc' in r['item']: print(r['source'], r['run'][:28], r['item'][:45], f"{r['recalc']:.4f}" if isinstance(r['recalc'], float) else r['recalc'], r['pushed'], r['agree'])
