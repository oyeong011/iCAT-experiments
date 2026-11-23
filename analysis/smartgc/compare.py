#!/usr/bin/env python3
"""11-23 SmartGC vs CAT-47 vs iCAT V4 on mixY (20 x 1800 s). Reads existing result files only.
Writes result/smartgc-20261119/report/{compare.csv,phase_waf.csv,memory_measured.csv,fig*.png}."""
import csv, re, statistics as st
from pathlib import Path
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]; S = ROOT/'result/smartgc-20261119'; R = ROOT/'result/gc-20261010'
OUT = S/'report'; OUT.mkdir(exist_ok=True)
RUNS = [  # label, policy, run dir, samples/commit/sha prefix
    ('SmartGC-EQ8', 'smartgc-eq8', R/'mixY-smartgc-eq8-rep1', S/'smartgc-eq8-rep1'),
    ('SmartGC', 'smartgc', S/'resume/mixY-smartgc-rep1', S/'resume/smartgc-rep1'),
    ('CAT-47', 'sg-arm47', R/'mixY-sg-arm47-rep1', S/'sg-arm47-rep1'),
    ('iCAT V4', 'onlinev4', S/'resume/mixY-onlinev4-rep1', S/'resume/onlinev4-rep1')]
V4_NET_NS_PER_GC = 9.4  # resource-v124-20261114 report, FIO-Fast, n=3 (different workload -> estimate only)
kv = lambda line: dict(t.split('=', 1) for t in line.split() if '=' in t)

def parse(label, pol, d, pre):
    r = {'label': label, 'policy': pol, 'dir': str(d.relative_to(ROOT)),
         'exit': (d/'exit-code.txt').read_text().strip(),
         'sha256': Path(f'{pre}.module.sha256').read_text().split()[0],
         'commit': Path(f'{pre}.commit.txt').read_text().strip()[:9]}
    tot = kv(next(l for l in (d/'summary.txt').read_text().splitlines() if l.startswith('total')))
    r['host_pages'], r['gc_pages'] = int(tot['host_pages']), int(tot['gc_pages'])
    r['host_TB'] = int(tot['host_bytes']) / 1e12
    r['WAF'] = 1 + r['gc_pages'] / r['host_pages']
    fc = (d/'final-control.txt').read_text().splitlines()
    r['gc_count'] = sum(int(kv(l)['gc_count']) for l in fc if l.startswith('part='))
    sg = [kv(l) for l in fc if l.startswith('smartgc part=')]
    if sg:  # SMARTGC builds only: nand_pages includes GC-buffer absorption (SMARTGC_RUN_GUIDE.md section 5)
        r['nand_pages'] = sum(int(x['nand_pages']) for x in sg)
        r['steps'] = sum(int(x['steps']) for x in sg)
    else:   # no GC buffer: every host and GC page is one NAND program
        r['nand_pages'] = r['host_pages'] + r['gc_pages']; r['steps'] = None
    r['WAF_nand'] = r['nand_pages'] / r['host_pages']
    r['phases'] = [float(m) for m in re.findall(r'^phaseS\d\d\(\w+\).*WAF=([\d.]+)', (d/'summary.txt').read_text(), re.M)]
    # samples: CPU (schedstat ns) and kernel memory (kB)
    rows = []
    for l in Path(f'{pre}.samples.txt').read_text().splitlines():
        t, tag = float(l.split()[0]), re.search(r'tag=(\w+)', l)[1]
        m = {k: int(v) for k, v in re.findall(r'(\w+)=(\d+) ', l.split('threads=')[0])}
        th = {c: int(ns) for c, ns in re.findall(r'\d+:(nvmev_\w+?):(\d+):', l)}
        rows.append((t, tag, m, th))
    run = [x for x in rows if x[1] == 'run' and x[3]]
    wall = run[-1][0] - run[0][0]
    for c, k in (('nvmev_dispatcher', 'disp'), ('nvmev_io_worker_0', 'iow')):
        r[f'{k}_cpu_s'] = (run[-1][3][c] - run[0][3][c]) / 1e9
        r[f'{k}_util'] = r[f'{k}_cpu_s'] / wall
    r['wall_h'] = wall / 3600
    r['coresize'] = run[0][2].get('coresize')
    before = next((x for x in rows if x[1] == 'before'), None)
    for k in ('VmallocUsed', 'Slab', 'SUnreclaim', 'Percpu'):
        r[f'{k}_run_kB'] = st.mean(x[2][k] for x in run)
        r[f'{k}_before_kB'] = before[2][k] if before else None
        r[f'{k}_delta_kB'] = r[f'{k}_run_kB'] - before[2][k] if before else None
    r['learn_cpu_s'] = r['gc_count'] * V4_NET_NS_PER_GC / 1e9 if pol == 'onlinev4' else None
    return r

runs = [parse(*x) for x in RUNS]
cols = ['label', 'policy', 'exit', 'commit', 'sha256', 'host_TB', 'host_pages', 'gc_pages', 'nand_pages', 'gc_count', 'steps',
        'WAF', 'WAF_nand', 'disp_cpu_s', 'iow_cpu_s', 'disp_util', 'iow_util', 'wall_h', 'learn_cpu_s',
        'VmallocUsed_before_kB', 'VmallocUsed_run_kB', 'VmallocUsed_delta_kB', 'Slab_before_kB', 'Slab_run_kB', 'Slab_delta_kB',
        'SUnreclaim_run_kB', 'Percpu_run_kB', 'coresize', 'dir']
with open(OUT/'compare.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(cols)
    for r in runs: w.writerow(['미측정' if r.get(c) is None else (f'{r[c]:.6g}' if isinstance(r[c], float) else r[c]) for c in cols])
with open(OUT/'phase_waf.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['phase'] + [r['label'] for r in runs])
    for i in range(20): w.writerow([f'S{i+1:02d}'] + [r['phases'][i] for r in runs])

C = {'SmartGC-EQ8': '#d95f02', 'SmartGC': '#e7298a', 'CAT-47': '#7570b3', 'iCAT V4': '#1b9e77'}
L = [r['label'] for r in runs]
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
x = range(len(runs))
ax[0].bar([i - .2 for i in x], [r['WAF'] for r in runs], .4, label='WAF (1 + GC/host)', color=[C[l] for l in L])
ax[0].bar([i + .2 for i in x], [r['WAF_nand'] for r in runs], .4, label='WAF_nand (NAND programs/host)', color=[C[l] for l in L], alpha=.45, hatch='//')
for i, r in enumerate(runs): ax[0].text(i - .2, r['WAF'] + .15, f"{r['WAF']:.2f}", ha='center', fontsize=8)
ax[0].set_xticks(list(x), L); ax[0].set_ylabel('WAF (lower is better)'); ax[0].legend(fontsize=8); ax[0].set_title('(a) Write amplification, mixY 10 h')
ax[1].bar(L, [r['host_TB'] for r in runs], color=[C[l] for l in L])
for i, r in enumerate(runs): ax[1].text(i, r['host_TB'] + .1, f"{r['host_TB']:.2f}", ha='center', fontsize=8)
ax[1].set_ylabel('Host data written in 10 h (TB)'); ax[1].set_title('(b) Work done in the same 20 x 1800 s')
fig.tight_layout(); fig.savefig(OUT/'fig1_waf_throughput.png', dpi=150)

fig, ax = plt.subplots(figsize=(11, 4))
for r in runs: ax.plot(range(1, 21), r['phases'], marker='o', ms=3, label=r['label'], color=C[r['label']])
ax.set_xticks(range(1, 21), [f'S{i}\n{w}' for i, w in zip(range(1, 21), 'F S V F V S F S V F V S F S V F V S F S'.split())], fontsize=7)
ax.set_ylabel('Phase WAF'); ax.set_yscale('log'); ax.legend(); ax.set_title('Per-phase WAF (F = FIO test4, S = FIO test3, V = Varmail)')
fig.tight_layout(); fig.savefig(OUT/'fig2_phase_waf.png', dpi=150)

# memory: measured (VmallocUsed, run mean - before, n = 1) vs calculated from code + sizeof
CALC = [('SmartGC / SmartGC-EQ8', 2343936, 'Q-table 640,000 + victim list/sort/drain/GC-buffer bitmap arrays 1,703,936 B (smartgc_memory_sizes.csv)'),
        ('CAT-47', 0, 'no learner state'),
        ('iCAT V4', 10112, 'sizeof learner state, resource-v124-20261114 report')]
with open(OUT/'memory_calculated.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['policy', 'bytes_4_partitions', 'basis']); w.writerows(CALC)
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
m = [(r['label'], r['VmallocUsed_delta_kB']) for r in runs]
ax[0].bar([l for l, v in m], [v or 0 for l, v in m], color=[C[l] for l, v in m])
for i, (l, v) in enumerate(m): ax[0].text(i, (v or 0) + 300, 'not measured' if v is None else f'{v/1024:.1f} MB', ha='center', fontsize=8)
ax[0].set_ylabel('VmallocUsed, run mean - before load (kB)'); ax[0].set_title('(a) MEASURED kernel vmalloc growth (n = 1)')
ax[1].bar(['SmartGC', 'CAT-47', 'iCAT V4'], [b for _, b, _ in CALC], color=[C['SmartGC'], C['CAT-47'], C['iCAT V4']]); ax[1].set_yscale('log'); ax[1].set_ylim(1, 1e7)
for i, (_, b, _) in enumerate(CALC): ax[1].text(i, max(b, 1) * 1.3, f'{b:,} B', ha='center', fontsize=8)
ax[1].set_ylabel('bytes, 4 partitions (log)'); ax[1].set_title('(b) CALCULATED learner/policy state (code + sizeof)')
fig.tight_layout(); fig.savefig(OUT/'fig3_memory.png', dpi=150)

if __name__ == '__main__':
    for r in runs:
        assert r['exit'] == '0' and len(r['phases']) == 20, r['label']
        assert abs(r['WAF'] - float(re.search(r'total.*WAF=([\d.]+)', (ROOT/r['dir']/'summary.txt').read_text())[1])) < 1e-5
    print(open(OUT/'compare.csv').read())
