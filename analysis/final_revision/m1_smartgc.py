#!/usr/bin/env python3
"""M1 SmartGC vs iCAT: re-derive every measured number from the raw run directories (read-only), GoCom 2026-11-25.
    python3 -I analysis/final_revision/m1_smartgc.py
Runs: the four SeungCom mixY 10 h runs of result/smartgc-20261119/report/compare.csv (all November, same host, n=1 each).
Outputs result/final-revision-analysis/{m1_waf.csv, m1_latency_fio.csv, m1_latency_varmail.csv, m1_check.csv}.
Measured = recomputed from raw counters / fio json / filebench text. Nothing estimated here; memory sizes are in m5 (calculated)."""
import csv, json, re, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'result/final-revision-analysis'; OUT.mkdir(parents=True, exist_ok=True)
CMP = list(csv.DictReader(open(ROOT / 'result/smartgc-20261119/report/compare.csv')))
cnt = lambda t, k: int(re.search(rf'\b{k}=(\d+)', t)[1])
SEQ = 'F S V F V S F S V F V S F S V F V S F S'.split()   # mixY phases S01..S20 (report.md)


def w(name, rows):
    with open(OUT / name, 'w', newline='') as f:
        x = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r))); x.writeheader(); x.writerows(rows)


waf, fio, vm, chk = [], [], [], []
for c in CMP:
    d = ROOT / c['dir']; s = (d / 'summary.txt').read_text() if (d / 'summary.txt').exists() else ''
    t = re.search(r'^total .*host_pages=(\d+) gc_pages=(\d+)', s, re.M)
    if t: h, g = int(t[1]), int(t[2])
    else:   # failed first attempt keeps no summary; use stopped.txt or the last control-series line
        last = (d / 'control-series.txt').read_text().splitlines()[-1]; h, g = cnt(last, 'host_pages'), cnt(last, 'gc_pages')
    ps = re.findall(r'^part=\d host_pages=(\d+) gc_pages=(\d+)', (d / 'final-control.txt').read_text(), re.M) if (d / 'final-control.txt').exists() else []
    row = dict(policy=c['label'], run_dir=c['dir'], module_sha256=c['sha256'][:16], exit=(d / 'exit-code.txt').read_text().strip() if (d / 'exit-code.txt').exists() else 'missing',
               host_pages=h, gc_pages=g, waf=1 + g / h, waf_compare_csv=float(c['WAF']),
               waf_matches_report=abs(1 + g / h - float(c['WAF'])) < 5e-5,
               partition_sum_equal=(h, g) == (sum(int(a) for a, _ in ps), sum(int(b) for _, b in ps)) if ps else 'no final-control')
    for i, p in enumerate(SEQ, 1):
        a, b = d / f'phase-S{i:02d}-start.txt', d / f'phase-S{i:02d}-end.txt'
        if a.exists() and b.exists():
            x, y = a.read_text().splitlines()[0], b.read_text().splitlines()[0]
            row[f'S{i:02d}{p}'] = 1 + (cnt(y, 'gc_pages') - cnt(x, 'gc_pages')) / (cnt(y, 'host_pages') - cnt(x, 'host_pages'))
        j = d / f'phase-S{i:02d}.json'
        if p in 'FS' and j.exists():
            tx = j.read_text(); jj = json.loads(tx[tx.index('{'):])
            for jb in jj['jobs']:
                wr = jb['write']; pc = wr['clat_ns'].get('percentile', {})
                fio.append(dict(policy=c['label'], phase=f'S{i:02d}', kind='FIO test4' if p == 'F' else 'FIO test3', job=jb['jobname'],
                                rate_iops=jb['job options'].get('rate_iops', ''), iops=wr['iops'], rate_achieved=(float(wr['iops']) >= 0.999 * float(jb['job options']['rate_iops'])) if jb['job options'].get('rate_iops') else '',
                                clat_mean_us=wr['clat_ns']['mean'] / 1e3, clat_p50_us=pc.get('50.000000', 0) / 1e3, clat_p99_us=pc.get('99.000000', 0) / 1e3,
                                clat_p999_us=pc.get('99.900000', 0) / 1e3, error=jb.get('error', 0)))
        fb = d / f'filebench-S{i:02d}.txt'
        if p == 'V' and fb.exists():
            m = re.search(r'IO Summary: (\d+) ops ([\d.]+) ops/s .*?([\d.]+)mb/s\s+([\d.]+)ms/op', fb.read_text())
            if m: vm.append(dict(policy=c['label'], phase=f'S{i:02d}', ops=int(m[1]), ops_per_s=float(m[2]), mb_per_s=float(m[3]), ms_per_op=float(m[4])))
    waf.append(row)
w('m1_waf.csv', waf); w('m1_latency_fio.csv', fio); w('m1_latency_varmail.csv', vm)
summ = []
for c in CMP:
    f = [r for r in fio if r['policy'] == c['label']]; v = [r for r in vm if r['policy'] == c['label']]
    summ.append(dict(policy=c['label'], fio_phases=len({r['phase'] for r in f}), fio_jobs_rate_not_met=sum(r['rate_achieved'] is False for r in f), fio_errors=sum(r['error'] for r in f),
                     fio_p99_us_median_over_jobs=st.median(r['clat_p99_us'] for r in f) if f else '', fio_p50_us_median_over_jobs=st.median(r['clat_p50_us'] for r in f) if f else '',
                     varmail_phases=len(v), varmail_ops_per_s_mean=st.mean(r['ops_per_s'] for r in v) if v else '', varmail_ms_per_op_mean=st.mean(r['ms_per_op'] for r in v) if v else ''))
w('m1_check.csv', summ)
for r in waf: print(r['policy'], r['exit'], f"{r['waf']:.4f}", r['waf_matches_report'], r['partition_sum_equal'])
for r in summ: print(r)
