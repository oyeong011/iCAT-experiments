#!/usr/bin/env python3
"""GoCom independent re-check of SeungCom revision analyses (report/revision-20261123, main 2f6ae2dec).

Re-derives numbers from RAW files with code written here (not importing SeungCom's scripts):
  R1  random fixed-arm expectation (mixA, mixC, 1x): 45-arm mean from each run's summary.txt
  R2  GoCom revA Random vs V4 WAF: summary.txt total vs control-series counters (two paths)
  R3  recovery: SeungCom definition re-implemented + GoCom/revA definition on the same runs
  R4  exploration counts for the mixY V4 (Nov) and v7 (Oct) logs
Outputs: result/revision-gocom-20261123/verify_*.csv
"""
import csv, re, statistics as st, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'result/revision-gocom-20261123'; OUT.mkdir(parents=True, exist_ok=True)
M = ROOT / 'result/mix-20260911'


def total_waf(d):
    s = (d / 'summary.txt').read_text()
    m = re.search(r'^total .*host_pages=(\d+) gc_pages=(\d+)', s, re.M)
    return 1 + int(m[2]) / int(m[1]) if m else None


def ok(d):
    e = d / 'exit-code.txt'
    return e.exists() and e.read_text().strip() == '0'


# ---- R1 random fixed-arm expectation
r1 = []
for wl in ('mixA', 'mixC'):
    arms = {}
    for d in sorted(M.glob(f'{wl}-arm[0-9][0-9]-rep*')):
        if not d.is_dir() or not ok(d) or not (d / 'summary.txt').exists(): continue
        if re.search(r'-x\d|smoke|broken', d.name): continue
        a = int(re.search(r'arm(\d\d)', d.name)[1])
        w = total_waf(d)
        if w: arms.setdefault(a, []).append(w)
    per = {a: st.mean(v) for a, v in arms.items() if a >= 15}
    sc = {'mixA': (1.9546, 1.9390, 1.7158, 47, 2.2286), 'mixC': (1.9496, 1.9304, 1.7502, 47, 2.2199)}[wl]
    best = min(per, key=per.get)
    r1.append((wl, len(per), st.mean(per.values()), st.median(per.values()), per[best], best, max(per.values()), *sc,
               sorted(set(range(15, 60)) - set(per))))
with open(OUT / 'verify_R1_random_fixed.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['workload', 'arms_found_15_59', 'mean_45', 'median_45', 'best', 'best_arm', 'worst',
                'seung_mean', 'seung_median', 'seung_best', 'seung_best_arm', 'seung_worst', 'missing_arms'])
    w.writerows(r1)

# ---- R2 revA Random/V4: two independent WAF paths
r2 = []
for d in sorted((ROOT / 'result/revA-20261114/raw').glob('mixFYF-revA-*-rep[0-9]')):
    ser = []
    for l in (d / 'control-series.txt').read_text().splitlines():
        kv = dict(re.findall(r'(\w+)=(\d+)', l))
        if 'host_pages' in kv and kv.get('active') == '1': ser.append((int(l.split()[0]), int(kv['host_pages']), int(kv['gc_pages'])))
    t0 = dt.datetime.fromisoformat((d / 'phase-A-start.time').read_text().strip()).timestamp()
    t1 = dt.datetime.fromisoformat((d / 'phase-C-end.time').read_text().strip()).timestamp()
    a = min(ser, key=lambda x: abs(x[0] - t0)); b = min(ser, key=lambda x: abs(x[0] - t1))
    r2.append((d.name, total_waf(d), 1 + (b[2] - a[2]) / (b[1] - a[1]), (b[1] - a[1])))
with open(OUT / 'verify_R2_waf_two_paths.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['run', 'WAF_summary_total', 'WAF_control_series_A_start_to_C_end', 'host_pages_series']); w.writerows(r2)


# ---- R3 recovery: both definitions
def series(d):
    s = []
    for l in (d / 'control-series.txt').read_text().splitlines():
        kv = dict(re.findall(r'(\w+)=(\d+)', l))
        if 'host_pages' in kv: s.append((int(l.split()[0]), int(kv['host_pages']), int(kv['gc_pages'])))
    return s


def phases(d):
    out = []
    for f in d.glob('phase-*-start.time'):
        n = f.name[len('phase-'):-len('-start.time')]; e = d / f'phase-{n}-end.time'
        if e.exists():
            out.append((n, dt.datetime.fromisoformat(f.read_text().strip()).timestamp(), dt.datetime.fromisoformat(e.read_text().strip()).timestamp()))
    return sorted(out, key=lambda x: x[1])


def wf(a, b): return 1 + (b[2] - a[2]) / max(b[1] - a[1], 1)


def rec_seung(s, t0, t1):
    """one-sided: rolling 10-sample WAF <= 1.05 x (2nd-half WAF) for this and the next 20 rolling windows."""
    p = [x for x in s if t0 <= x[0] <= t1]
    if len(p) < 32: return None, None, None
    h = [x for x in p if x[0] >= (t0 + t1) / 2]; ref = wf(h[0], h[-1])
    roll = [(p[i][0], wf(p[i - 10], p[i])) for i in range(10, len(p))]
    for i in range(len(roll) - 20):
        if all(w <= ref * 1.05 for _, w in roll[i:i + 21]): return ref, roll[i][0] - t0, roll[0][1] / ref
    return ref, None, roll[0][1] / ref


def rec_gocom(s, t0, t1):
    """two-sided (revA/adapt): trailing 300 s WAF within +-5% of last-600 s WAF for 180 s; search until t1-600."""
    p = [x for x in s if t0 <= x[0] <= t1]
    tail = [x for x in p if x[0] >= t1 - 600]
    if len(tail) < 2: return None, None
    ref = wf(tail[0], tail[-1]); run = None
    for i, x in enumerate(p):
        if x[0] > t1 - 600: break
        back = [y for y in p[:i + 1] if x[0] - y[0] <= 300]
        if x[0] - t0 < 300 or len(back) < 2: continue
        good = abs(wf(back[0], x) / ref - 1) <= .05
        if good:
            run = x[0] if run is None else run
            if x[0] - run >= 180: return ref, run - t0
        else:
            run = None
    return ref, None


seung = {(r['dir'], r['phase']): r for r in csv.DictReader(open(ROOT / 'report/revision-20261123/recovery.csv'))}
r3 = []
for (rel, ph), r in seung.items():
    d = ROOT / rel
    if not (d / 'control-series.txt').exists(): continue
    s = series(d); pr = {n: (a, b) for n, a, b in phases(d)}
    if ph not in pr: continue
    ref, rec, first_ratio = rec_seung(s, *pr[ph])
    gref, grec = rec_gocom(s, *pr[ph])
    sv = r['recovery_s']
    same = (sv == '' and rec is None) or (sv != '' and rec is not None and abs(float(sv) - rec) <= 31)
    r3.append((r['group'], r['policy'], ph, sv, rec, 'match' if same else 'DIFF', round(first_ratio, 3) if first_ratio else None,
               'starts at/below ref (one-sided rule passes at once)' if first_ratio is not None and first_ratio <= 1.05 else '',
               grec, rel))
with open(OUT / 'verify_R3_recovery.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['group', 'policy', 'phase', 'seung_recovery_s', 'gocom_reimpl_seung_def_s', 'check', 'first_window_waf_over_ref',
                'note', 'gocom_def_twosided_s', 'dir'])
    w.writerows(r3)

# ---- R4 exploration counts
r4 = []
for lab, rel in (('iCAT v4 mixY Nov', 'result/smartgc-20261119/resume/mixY-onlinev4-rep1'),
                 ('iCAT v7 mixY Oct (SeungCom)', 'result/v7-20261011/mixY/mixY-onlinev7-rep1')):
    kl = (ROOT / rel / 'kernel.log').read_text(errors='replace').splitlines()
    arms = {}
    reset_lines = shift_lines = settled = 0; reset_ts = []
    for l in kl:
        if 'WATGC_V2 sample' in l:
            kv = dict(re.findall(r'(\w+)=(\S+)', l)); arms.setdefault(kv['part'], []).append(int(kv['evaluated']))
        elif 'WATGC_V2 reset ' in l: reset_lines += 1
        elif 'WATGC_V6 shift-reset' in l: shift_lines += 1
        elif 'WATGC_V2 settled' in l: settled += 1
    r4.append((lab, sum(len(v) for v in arms.values()), sum(sum(a != b for a, b in zip(v, v[1:])) for v in arms.values()),
               len({a for v in arms.values() for a in v}), reset_lines, shift_lines, reset_lines - shift_lines, settled, rel))
with open(OUT / 'verify_R4_exploration.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['run', 'windows', 'arm_switches', 'distinct_arms', 'WATGC_V2_reset_lines', 'WATGC_V6_shift_reset_lines',
                                   'reset_lines_minus_shift (drift path, if every shift also prints a V2 reset)', 'settled', 'dir'])
    w.writerows(r4)

for x in r1: print('R1', x[:7], 'seung', x[7:12], 'missing', x[12])
for x in r2: print('R2', x)
print('R3 total', len(r3), 'match', sum(1 for x in r3 if x[5] == 'match'), 'immediate-pass', sum(1 for x in r3 if x[7]))
for x in r3:
    if x[5] != 'match': print('R3 diff', x)
for x in r4: print('R4', x)
