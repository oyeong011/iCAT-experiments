#!/usr/bin/env python3
"""M5 resource efficiency from EXISTING logs only (read-only). GoCom 2026-11-25.
    python3 -I analysis/final_revision/m5_resource.py GROUP=HOST:BATCH:GLOB [...]
Per run: FIO clat p50/p99 (phases A and C; jobs are rate-limited, so latency only), YCSB-A average / p99 latency and throughput
(phase B, time-based, not rate-limited), learner elapsed time (learner_ns = kernel ktime of the decision path, NOT CPU time),
number of decisions (windows), per-decision mean. Statistics only for groups with 3 valid runs; groups are never pooled.
Outputs result/final-revision-analysis/{latency_comparison.csv, cpu_overhead.csv, memory_overhead.csv, m5_stats.csv}."""
import csv, gzip, json, math, re, statistics as st, sys
from pathlib import Path
from scipy import stats
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis/final_e1'))
import validity as V
OUT = ROOT / 'result/final-revision-analysis'; OUT.mkdir(parents=True, exist_ok=True)


def w(name, rows):
    if rows:
        with open(OUT / name, 'w', newline='') as f:
            x = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r))); x.writeheader(); x.writerows(rows)


lat, cpu = [], []
for a in sys.argv[1:]:
    name, spec = a.split('=', 1); host, batch, glob = spec.split(':', 2)
    for d in sorted(p for p in (Path('/').glob(glob.lstrip('/')) if glob.startswith('/') else ROOT.glob(glob)) if p.is_dir()):
        rep = int(re.search(r'rep(\d)', d.name)[1]); ok = (d / 'exit-code.txt').exists() and (d / 'exit-code.txt').read_text().strip() == '0' and V.run_ok(d)
        r = dict(group=name, host=host, batch=batch, rep=rep, valid=ok, dir=str(d))
        for p in 'AC':
            j = d / f'phase-{p}.json'
            if not j.exists(): continue
            t = j.read_text(); jj = json.loads(t[t.index('{'):])
            for jb in jj['jobs']:
                wr = jb['write']; pc = wr['clat_ns'].get('percentile', {})
                r[f'{p}_{jb["jobname"]}_p50_us'] = pc.get('50.000000', 0) / 1e3; r[f'{p}_{jb["jobname"]}_p99_us'] = pc.get('99.000000', 0) / 1e3
                r[f'{p}_{jb["jobname"]}_rate_met'] = float(wr['iops']) >= 0.999 * float(jb['job options'].get('rate_iops', 0) or 0)
        y = d / 'ycsb-run-B.txt.gz'
        if y.exists():
            t = gzip.open(y, 'rt', errors='replace').read(); g = lambda k: float(re.search(rf'^\[{k}\], ([^,]+?), ([\d.]+)', t, re.M)[2]) if re.search(rf'^\[{k}\]', t, re.M) else None
            for op in ('READ', 'UPDATE'):
                m1 = re.search(rf'^\[{op}\], AverageLatency\(us\), ([\d.]+)', t, re.M); m2 = re.search(rf'^\[{op}\], 99thPercentileLatency\(us\), ([\d.]+)', t, re.M)
                r[f'B_{op.lower()}_avg_us'] = float(m1[1]) if m1 else None; r[f'B_{op.lower()}_p99_us'] = float(m2[1]) if m2 else None
            m = re.search(r'^\[OVERALL\], Throughput\(ops/sec\), ([\d.]+)', t, re.M); r['B_ycsb_ops_per_s'] = float(m[1]) if m else None
        lat.append(r)
        kl = (d / 'kernel.log').read_text(errors='replace') if (d / 'kernel.log').exists() else ''
        beg = [m.end() for m in re.finditer(r'mix-mixFYF-\S+ BEGIN', kl)]; own = kl[beg[-1]:] if beg else kl
        last = {}
        for m in re.finditer(r'WATGC_V2 (?:sample|summary) ns=\d+ part=(\d) .*?select=(\d+) .*?learner_ns=(\d+)', own):
            last[int(m[1])] = (int(m[2]), int(m[3]))
        win = len(re.findall(r'WATGC_V2 sample ', own))
        lns = sum(v[1] for v in last.values()) if last else None
        cpu.append(dict(group=name, host=host, batch=batch, rep=rep, valid=ok, decisions_windows=win, arm_switches=sum(v[0] for v in last.values()) if last else '',
                        learner_elapsed_ms_ktime=lns / 1e6 if lns is not None else 'n/a (no learner_ns counter in this module)',
                        per_decision_us=(lns / win / 1e3) if lns and win else '', measurement='kernel ktime elapsed of the decision path (observe + set_arm); NOT process CPU time; per-GC hook excluded',
                        dir=str(d)))
w('latency_comparison.csv', lat); w('cpu_overhead.csv', cpu)
# memory: calculated (gdb sizeof, resource_overhead_final.md section 3) and measured (SeungCom VmallocUsed, n=1)
mem = [dict(policy='iCAT V4 (online-v4, db93f822)', item='learner state, 4 partitions (tuner minus 128 B parameter cache)', bytes=10112, kind='calculated (gdb sizeof)', source='report/revision-20261123-gocom/resource_overhead_final.md#3.1'),
       dict(policy='iCAT V4 (online-v4, db93f822)', item='struct watgc_v2_tuner x 4 (whole)', bytes=10624, kind='calculated (gdb sizeof)', source='same'),
       dict(policy='iCAT revA/revC-v4 (987d6204 / revC)', item='struct watgc_v2_tuner x 4 incl. 56 B counters', bytes=10848, kind='calculated (gdb sizeof)', source='same'),
       dict(policy='SmartGC (smartgc-src)', item='learner state: Q-table 640,000 + candidates 1,048,576 + sort keys 262,144 + struct 928', bytes=1951648, kind='calculated (gdb sizeof + allocation formula)', source='same'),
       dict(policy='SmartGC (smartgc-src)', item='GC buffer (drain + page bitmap), not learner', bytes=393216, kind='calculated', source='same'),
       dict(policy='SmartGC paper as written', item='per-block 20 KB Q-table x 32,768 lines', bytes=32768 * 20 * 1024, kind='calculated from the paper text (not implemented)', source='smartgc-src/SMARTGC.md item 1'),
       dict(policy='CAT-47', item='learner state', bytes=0, kind='calculated', source='no learner')]
for c in csv.DictReader(open(ROOT / 'result/smartgc-20261119/report/compare.csv')):
    mem.append(dict(policy=c['label'], item='VmallocUsed delta, run mean - before load (kB)', bytes=(float(c['VmallocUsed_delta_kB']) * 1024) if c['VmallocUsed_delta_kB'] not in ('', '미측정') else 'not measured',
                    kind='measured, SeungCom mixY, n=1 (emulator itself ~35 MB; supporting evidence only)', source='result/smartgc-20261119/report/compare.csv'))
w('memory_overhead.csv', mem)
# stats per group (n=3 only)
srows = []
keys = sorted({k for r in lat for k in r if k.endswith(('_us', '_ops_per_s'))})
for g in dict.fromkeys(r['group'] for r in lat):
    for k in keys + ['learner_elapsed_ms_ktime', 'per_decision_us', 'decisions_windows']:
        src = cpu if k in ('learner_elapsed_ms_ktime', 'per_decision_us', 'decisions_windows') else lat
        v = [r[k] for r in src if r['group'] == g and r['valid'] and isinstance(r.get(k), (int, float))]
        if not v: continue
        row = dict(group=g, metric=k, n=len(v), values=' / '.join(f'{x:.3f}' for x in v))
        if len(v) >= 3:
            m, s = st.mean(v), st.stdev(v); h = stats.t.ppf(.975, len(v) - 1) * s / math.sqrt(len(v)); row.update(mean=m, sd=s, ci_lo=m - h, ci_hi=m + h)
        else: row['mean'] = 'n<3: no statistics'
        srows.append(row)
w('m5_stats.csv', srows)
for r in srows:
    if r['metric'] in ('A_hot_p99_us', 'C_hot_p99_us', 'B_read_p99_us', 'B_update_avg_us', 'B_ycsb_ops_per_s', 'learner_elapsed_ms_ktime', 'per_decision_us'):
        print(r['group'], r['metric'], r['values'], f"{r['mean']:.3f}" if isinstance(r['mean'], float) else r['mean'])
