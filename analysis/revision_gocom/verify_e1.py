#!/usr/bin/env python3
"""GoCom independent check of SeungCom E1 (mixR x3: online-v4 / v4nodrift / v4fullreset) from raw files.
Re-runnable as more runs arrive. Reference: Sept mixR-onlinev4-rep{1,2}-x3 (same module db93f822, same seeds per rep).
Outputs (new files only): result/revision-gocom-20261123/e1_{runs,phases,resets,recovery,stats}.csv"""
import csv, re, glob, hashlib, statistics as st, datetime as dt, math, os, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / 'result/revision-gocom-20261123'
E1 = sorted(d for d in (ROOT / 'result/revision-20261123/mixR').glob('mixR-online*-rep[0-9]-x3') if d.is_dir())
REF = sorted(d for d in (ROOT / 'result/mix-20260911').glob('mixR-onlinev4-rep[0-9]-x3') if d.is_dir())
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 8: 2.306, 10: 2.228}

def cnt(p):
    m = re.search(r'host_pages=(\d+) gc_pages=(\d+)', p.read_text()); return int(m[1]), int(m[2])
def parts(p): return {int(a): (int(b), int(c)) for a, b, c in re.findall(r'part=(\d) host_pages=(\d+) gc_pages=(\d+)', p.read_text())}
def ts(p): return dt.datetime.fromisoformat(p.read_text().strip()).timestamp()
def wf(h, g): return 1 + g / h if h else float('nan')
def env(d, pat):
    for l in (d / 'environment.txt').read_text().splitlines():
        if re.search(pat, l): return l.strip()
    return ''
def klog(d):
    txt = ''
    for f in [d / 'kernel.log', d / 'kernel-final.log', *sorted((d / 'kernel-snapshots').glob('*.log'))]:
        if f.exists(): txt += f.read_text(errors='replace')
    z = d / 'kernel.log.zst'
    if z.exists(): txt += subprocess.run(['zstdcat', str(z)], capture_output=True, text=True).stdout
    return sorted(set(txt.splitlines()))

runs, phs, resets, recs = [], [], [], []
for d in E1 + REF:
    grp = 'E1-nov' if 'revision-20261123' in str(d) else 'ref-sep'
    pol = re.search(r'mixR-(online\w+?)-rep', d.name)[1]; rep = int(re.search(r'rep(\d)', d.name)[1])
    ok = (d / 'exit-code.txt').exists() and (d / 'exit-code.txt').read_text().strip() == '0'
    summ = (d / 'summary.txt').read_text()
    th, tg = map(int, re.search(r'^total .*host_pages=(\d+) gc_pages=(\d+)', summ, re.M).groups())
    fp = parts(d / 'final-control.txt'); ph_sum = sum(v[0] for v in fp.values()); pg_sum = sum(v[1] for v in fp.values())
    seeds = re.findall(r'"randseed" : "(\d+)"', (d / 'phase-A.json').read_text())[:1] + re.findall(r'"randseed" : "(\d+)"', (d / 'phase-C.json').read_text())[:1]
    ko = env(d, r'\.ko$').split()[0][:12]
    lines = klog(d)
    mark = {m[2]: float(m[1]) for l in lines for m in [re.match(r'\[\s*([\d.]+)\] mix-\S+ phase=(\w) START', l)] if m}
    mark.update({m[2] + '_end': float(m[1]) for l in lines for m in [re.match(r'\[\s*([\d.]+)\] mix-\S+ phase=(\w) END', l)] if m})
    rs = [(float(m[1]), int(m[2]), int(m[3]), m[4], m[5]) for l in lines
          for m in [re.match(r'\[\s*([\d.]+)\] NVMeVirt: WATGC_V2 reset .*part=(\d) .*window=(\d+) arm=(\d+) reason=(\S+)', l)] if m]
    for t, part, win, arm, why in rs:
        ph = max((p for p in 'ABC' if p in mark and mark[p] <= t), default='?')
        resets.append(dict(group=grp, policy=pol, rep=rep, part=part, window=win, arm_at_reset=arm, reason=why, phase=ph,
                           s_after_phase_start=round(t - mark.get(ph, float('nan')), 1)))
    runs.append(dict(group=grp, policy=pol, rep=rep, exit_ok=ok, module=ko, fio_seeds='/'.join(seeds), start=env(d, r'^20\d\d-'),
                     waf_summary=f'{wf(th, tg):.6f}', waf_partition_sum=f'{wf(ph_sum, pg_sum):.6f}', paths_equal=(th, tg) == (ph_sum, pg_sum),
                     resets=len(rs), resets_A=sum(r[0] < mark.get('B', 9e18) for r in rs),
                     resets_B=sum(mark.get('B', 9e18) <= r[0] < mark.get('C', 9e18) for r in rs), resets_C=sum(r[0] >= mark.get('C', 9e18) for r in rs),
                     dir=str(d.relative_to(ROOT))))
    # phases: counter diff, and summary
    for p in 'ABC':
        (h0, g0), (h1, g1) = cnt(d / f'phase-{p}-start.txt'), cnt(d / f'phase-{p}-end.txt')
        sm = re.search(rf'^phase{p}\(\S+\) host_pages=(\d+) gc_pages=(\d+) WAF=([\d.]+)', summ, re.M)
        phs.append(dict(group=grp, policy=pol, rep=rep, phase=p, host_pages=h1 - h0, gc_pages=g1 - g0, waf_recalc=f'{wf(h1-h0, g1-g0):.6f}',
                        waf_summary=sm[3], match=(h1 - h0, g1 - g0) == (int(sm[1]), int(sm[2]))))
    # recovery after transitions, both definitions (same code as verify_seungcom.py R3)
    ser = []
    for l in (d / 'control-series.txt').read_text().splitlines():
        kv = dict(re.findall(r'(\w+)=(\d+)', l))
        if 'host_pages' in kv: ser.append((int(l.split()[0]), int(kv['host_pages']), int(kv['gc_pages'])))
    for p in 'BC':
        t0, t1 = ts(d / f'phase-{p}-start.time'), ts(d / f'phase-{p}-end.time')
        pp = [x for x in ser if t0 <= x[0] <= t1]
        w = lambda a, b: 1 + (b[2] - a[2]) / max(b[1] - a[1], 1)
        # SeungCom one-sided
        h = [x for x in pp if x[0] >= (t0 + t1) / 2]; ref1 = w(h[0], h[-1]); r1 = None
        roll = [(pp[i][0], w(pp[i - 10], pp[i])) for i in range(10, len(pp))]
        for i in range(len(roll) - 20):
            if all(v <= ref1 * 1.05 for _, v in roll[i:i + 21]): r1 = roll[i][0] - t0; break
        # GoCom two-sided
        tail = [x for x in pp if x[0] >= t1 - 600]; ref2 = w(tail[0], tail[-1]); r2 = None; run = None
        for i, x in enumerate(pp):
            if x[0] > t1 - 600: break
            back = [y for y in pp[:i + 1] if x[0] - y[0] <= 300]
            if x[0] - t0 < 300 or len(back) < 2: continue
            if abs(w(back[0], x) / ref2 - 1) <= .05:
                run = x[0] if run is None else run
                if x[0] - run >= 180: r2 = run - t0; break
            else: run = None
        recs.append(dict(group=grp, policy=pol, rep=rep, phase=p, seung_onesided_ref=f'{ref1:.4f}', seung_onesided_s=r1,
                         first_window_over_ref=f'{roll[0][1] / ref1:.3f}', gocom_twosided_ref=f'{ref2:.4f}', gocom_twosided_s=r2))

def wcsv(name, rows):
    with open(OUT / name, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
wcsv('e1_runs.csv', runs); wcsv('e1_phases.csv', phs); wcsv('e1_resets.csv', resets); wcsv('e1_recovery.csv', recs)

# stats per (group, policy): mean, SD, t-CI; Welch vs online-v4 in E1 when n>=2 on both sides
stats = []
by = {}
for r in runs:
    if r['exit_ok']: by.setdefault((r['group'], r['policy']), []).append(float(r['waf_summary']))
for (g, p), v in sorted(by.items()):
    n = len(v); m = st.mean(v); sd = st.stdev(v) if n > 1 else float('nan')
    ci = T95.get(n - 1, 2.0) * sd / math.sqrt(n) if n > 1 else float('nan')
    row = dict(group=g, policy=p, n=n, mean=f'{m:.4f}', sd=f'{sd:.4f}', ci95=f'[{m-ci:.4f}, {m+ci:.4f}]' if n > 1 else 'n<2', welch_vs_E1_v4='')
    base = by.get(('E1-nov', 'onlinev4'), [])
    if g == 'E1-nov' and p != 'onlinev4' and n > 1 and len(base) > 1:
        a, b = v, base; va, vb = st.variance(a) / len(a), st.variance(b) / len(b); diff = st.mean(a) - st.mean(b)
        df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)); se = math.sqrt(va + vb)
        tq = T95.get(max(1, round(df)), 2.0) if round(df) in T95 else T95[min(T95, key=lambda k: abs(k - df))]
        row['welch_vs_E1_v4'] = f'{diff:+.4f} [{diff - tq*se:+.4f}, {diff + tq*se:+.4f}] df={df:.1f}'
    stats.append(row)
wcsv('e1_stats.csv', stats)
for f in ['e1_runs.csv', 'e1_stats.csv', 'e1_resets.csv', 'e1_recovery.csv']:
    print('==', f); print(open(OUT / f).read())
print('phase mismatches:', sum(not r['match'] for r in phs), 'of', len(phs))
