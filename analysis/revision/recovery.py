#!/usr/bin/env python3
"""Workload-switch recovery from existing runs (no new experiments).

Definitions (fixed before computing, see report/revision-20261123/workload_recovery_analysis.md):
  interval WAF   1 + dGC/dHost over a rolling 10-sample (5 min) window of control-series.txt (30 s samples)
  reference      the run's own host-weighted WAF over the second half of the phase (own steady state)
  recovered at   end of the first rolling window, after the phase start, whose WAF <= 1.05 x reference and
                 every rolling window in the next 10 min (20 samples) also is <= 1.05 x reference  (one-sided, recovery_s)
  two-sided      same, but |WAF/reference - 1| <= 0.05 (recovery2_s); first_window = recovered at the first window
                 (11-23: GoCom showed the one-sided rule passes 106/170 phases at the first window)
  recovery time  recovered_at - phase start (s); 'none' if never within the phase
Learner events come from kernel.log: phase START markers and WATGC reset/settled/sample lines share one clock.
"""
import csv, re, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'report/revision-20261123'; OUT.mkdir(parents=True, exist_ok=True)
TOL, ROLL, HOLD = 1.05, 10, 20

RUNS = {  # group: [(label, dir)], each group = one workload in one period
 'mixR-Sep (FIO-Fast -> YCSB-A -> FIO-Fast, x3)': [(p, f'result/mix-20260911/mixR-{d}-x3') for p, d in [
    ('iCAT v1', 'online-rep1'), ('iCAT v3', 'onlinev3-rep1'), ('iCAT v4 #1', 'onlinev4-rep1'), ('iCAT v4 #2', 'onlinev4-rep2'),
    ('arm 47', 'fixed47-rep1'), ('arm 50', 'fixed50-rep1'), ('arm 37', 'fixed37-rep1'), ('arm 17', 'arm17-rep1'), ('arm 32', 'arm32-rep1'), ('Greedy', 'greedy-rep1')]],
 'mixY-Oct (20 x 1800 s)': [('iCAT v7', 'result/v7-20261011/mixY/mixY-onlinev7-rep1'), ('iCAT v6', 'result/gc-20261010/mixY-onlinev6-rep1'),
    ('arm 47', 'result/gc-20261010/mixY-fixed47-rep1'), ('arm 50', 'result/gc-20261010/mixY-arm50-rep1'), ('arm 37', 'result/gc-20261010/mixY-arm37-rep1')],
 'mixY-Nov (20 x 1800 s)': [('iCAT v4', 'result/smartgc-20261119/resume/mixY-onlinev4-rep1'), ('arm 47 (sg)', 'result/gc-20261010/mixY-sg-arm47-rep1')],
}
# E1 (revision queue): every passing mixR x3 run, labelled by policy and rep.
# 11-24: result/revision-20261123/mixR is excluded (600k records -> SQLITE_FULL, YCSB failed 10-100% while exit=0).
# Reruns live in result/revision-20261124/mixR; a run counts only with exit 0 AND the runner's YCSB check file.
NAMES = {'onlinev4': 'iCAT v4', 'onlinev4nodrift': 'v4 nodrift', 'onlinev4fullreset': 'v4 fullreset', 'fixed47': 'arm 47'}
for d in sorted((ROOT/'result/revision-20261124/mixR').glob('mixR-*-rep*-x3')):
    m = re.match(r'mixR-(\w+)-rep(\d)-x3$', d.name)
    if m and (d/'ycsb-check.txt').exists() and (d/'exit-code.txt').exists() and (d/'exit-code.txt').read_text().strip() == '0':
        RUNS.setdefault('mixR-Nov E1 (x3)', []).append((f"{NAMES.get(m[1], m[1])} #{m[2]}", str(d.relative_to(ROOT))))
iso = lambda s: datetime.fromisoformat(s.strip()).timestamp()

def phases(d):
    out = []
    for f in sorted(d.glob('phase-*-start.time')):
        name = f.name[6:-11]
        e = d/f'phase-{name}-end.time'
        if e.exists(): out.append((name, iso(f.read_text()), iso(e.read_text())))
    return sorted(out, key=lambda x: x[1])

def series(d):
    s = []
    for l in (d/'control-series.txt').read_text().splitlines():
        m = re.match(r'(\d+) .*host_pages=(\d+) gc_pages=(\d+)', l)
        if m: s.append(tuple(int(x) for x in m.groups()))
    return s

def recovery(s, t0, t1):
    pts = [x for x in s if t0 <= x[0] <= t1]
    if len(pts) < ROLL + HOLD + 2: return None, (None, False, None, False), None
    waf = lambda a, b: 1 + (b[2] - a[2]) / max(b[1] - a[1], 1)
    half = [x for x in pts if x[0] >= (t0 + t1) / 2]
    ref = waf(half[0], half[-1])
    roll = [(pts[i][0], waf(pts[i - ROLL], pts[i])) for i in range(ROLL, len(pts))]
    def first(ok):
        for i, (t, w) in enumerate(roll):
            if i + HOLD < len(roll) and all(ok(x[1]) for x in roll[i:i + HOLD + 1]):
                return t - t0, i == 0
        return None, False
    one, f1 = first(lambda w: w <= ref * TOL)
    two, f2 = first(lambda w: abs(w / ref - 1) <= TOL - 1)
    return ref, (one, f1, two, f2), waf(pts[0], pts[-1])

def events(d):
    """per phase: first reset (detection), settled after it, windows between, all relative to phase START."""
    log = (d/'kernel.log').read_text(errors='replace').splitlines()
    start, ev = {}, []
    for l in log:
        m = re.match(r'\[\s*([\d.]+)\].*phase=(\w+) START', l)
        if m: start[m[2]] = float(m[1]); continue
        m = re.match(r'\[\s*([\d.]+)\] NVMeVirt: WATGC_V\d (reset|shift-reset|settled|sample) .*part=(\d)', l)
        if m: ev.append((float(m[1]), m[2], int(m[3])))
    res = {}
    names = sorted(start, key=start.get)
    for j, p in enumerate(names):
        t0, t1 = start[p], start[names[j + 1]] if j + 1 < len(names) else 1e18
        e = [x for x in ev if t0 <= x[0] < t1]
        resets = [x for x in e if x[1] in ('reset', 'shift-reset')]
        r = {'resets': len([x for x in e if x[1] == 'reset']), 'windows': sum(x[1] == 'sample' for x in e)}
        if resets:
            r0 = min(resets)[0]
            r['detect_s'] = r0 - t0
            st = [x[0] for x in e if x[1] == 'settled' and x[0] > r0]
            r['resettle_s'] = (min(st) - r0) if st else None
            r['explore_windows'] = sum(1 for x in e if x[1] == 'sample' and r0 < x[0] <= (min(st) if st else t1))
        res[p] = r
    return res

rows = []
for grp, runs in RUNS.items():
    for label, rel in runs:
        d = ROOT/rel
        if not (d/'control-series.txt').exists(): print('missing', rel, file=sys.stderr); continue
        s, ev = series(d), events(d) if not label.startswith(('arm', 'Greedy')) else {}
        for p, t0, t1 in phases(d):
            ref, rec, pw = recovery(s, t0, t1)
            e = ev.get(p, {})
            rows.append({'group': grp, 'policy': label, 'phase': p, 'phase_s': round(t1 - t0), 'phase_waf': pw and round(pw, 4),
                         'ref_waf_2nd_half': ref and round(ref, 4), 'recovery_s': rec[0], 'first_window': rec[1],
                         'recovery2_s': rec[2], 'first_window2': rec[3],
                         'resets': e.get('resets'), 'detect_s': e.get('detect_s') and round(e['detect_s']),
                         'resettle_s': e.get('resettle_s') and round(e['resettle_s']), 'explore_windows': e.get('explore_windows'),
                         'windows': e.get('windows'), 'dir': rel})
with open(OUT/'recovery.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
if __name__ == '__main__':
    assert rows and all(r['phase_s'] > 0 for r in rows)
    for r in rows: print({k: v for k, v in r.items() if k != 'dir'})
