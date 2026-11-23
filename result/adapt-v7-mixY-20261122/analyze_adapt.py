#!/usr/bin/env python3
"""adapt-v7-mixY-20261122: workload-change response of iCAT-v7 in the existing GoCom mixY run.

Input (read-only): result/v7-20261011-icat2/mixY/mixY-onlinev7-rep1 (host oy-B550M-DS3H, 2026-10-12).
Nothing is re-run.  Every time below comes from a log line; derived quantities are labelled.

Per transition (start of S02..S20) and per FTL partition:
  detect_s     first WATGC_V2 reset (both v6 shift-reset and settled waf-drift paths print it) after the
               phase START marker and before the phase END marker, seconds after the marker.  The reset
               line is both the detection and the start of re-exploration (same kernel call).
  cover_s      DERIVED: first sample after that reset whose active count is below the count logged right
               after the reset.  Elimination only runs once every active arm has been visited
               (watgc_v2_covered), so this is the earliest logged evidence that the re-sweep finished.
  settle_s     first WATGC_V2 settled line after that reset, within the phase.
  missing value = event not in the log within the phase ("none"); never interpolated.
Per phase: WAF recovery from the 30 s device counter series (all partitions together):
  trailing 300 s WAF w(t); target = WAF over the phase's last 600 s; recovered at the first t after the
  marker where |w - target| <= 5% target for 180 s in a row, searched until 600 s before the phase end;
  otherwise not_recovered.  Same rule as revA-20261114.
Exploration cost per phase: accepted windows (sample lines) and windows with evaluated != best.
"""
import csv, json, re, statistics as st, datetime as dt
from pathlib import Path

RAW = Path('/home/oy/iCAT/result/v7-20261011-icat2/mixY/mixY-onlinev7-rep1')
OUT = Path('/home/oy/iCAT/result/adapt-v7-mixY-20261122')
SEQ = 'F S V F V S F S V F V S F S V F V S F S'.split()
NAME = {'F': 'FIO-Fast', 'S': 'FIO-Slow', 'V': 'Varmail'}

ts_re = re.compile(r'^\[\s*(\d+\.\d+)\]')
kv = lambda s: dict(re.findall(r'(\w+)=(\S+)', s))

marks, resets, shifts, settles, samples = {}, [], [], [], []
for line in open(RAW / 'kernel.log', errors='replace'):
    m = ts_re.match(line)
    if not m:
        continue
    t = float(m.group(1))
    if 'mix-mixY-onlinev7' in line and 'phase=' in line and (' START' in line or ' END' in line):
        p = re.search(r'phase=(S\d\d) (START|END)', line)
        marks[(p.group(1), p.group(2))] = t
    elif 'WATGC_V2 reset ' in line:
        d = kv(line); resets.append((t, int(d['part']), d))
    elif 'WATGC_V6 shift-reset' in line:
        d = kv(line); shifts.append((t, int(d['part'])))
    elif 'WATGC_V2 settled ' in line:
        d = kv(line); settles.append((t, int(d['part'])))
    elif 'WATGC_V2 sample ' in line:
        d = kv(line); samples.append((t, int(d['part']), int(d['active']), int(d['evaluated']), int(d['best'])))

shift_ts = {(round(t, 3), p) for t, p in shifts}
def within(ev, a, b, part):
    return [x for x in ev if a <= x[0] < b and x[1] == part]

# device WAF series (wall clock); phase wall starts from *.time files
ser = []
for line in open(RAW / 'control-series.txt'):
    f = line.split(); d = kv(line)
    if 'host_pages' in d:
        ser.append((int(f[0]), int(d['host_pages']), int(d['gc_pages'])))
wall = {s: dt.datetime.fromisoformat((RAW / f'phase-{s}-{e}.time').read_text().strip()).timestamp()
        for s in [f'S{i:02d}' for i in range(1, 21)] for e in ('start',) }
wall_end = {s: dt.datetime.fromisoformat((RAW / f'phase-{s}-end.time').read_text().strip()).timestamp()
            for s in [f'S{i:02d}' for i in range(1, 21)]}

def wtrail(t, span):
    a = [x for x in ser if t - span <= x[0] <= t]
    if len(a) < 2 or a[-1][1] == a[0][1]:
        return None
    return 1 + (a[-1][2] - a[0][2]) / (a[-1][1] - a[0][1])

def recovery(s):
    t0, t1 = wall[s], wall_end[s]
    target = wtrail(t1, 600)
    run = None
    for x in ser:
        if not (t0 < x[0] <= t1 - 600):
            continue
        w = wtrail(x[0], 300)
        ok = w is not None and target and abs(w - target) <= 0.05 * target
        if ok:
            run = run if run is not None else x[0]
            if x[0] - run >= 180:
                return target, run - t0
        else:
            run = None
    return target, None

rows, phase_rows = [], []
for i in range(1, 21):
    s = f'S{i:02d}'; a = marks[(s, 'START')]; b = marks[(s, 'END')]
    target, rec = recovery(s)
    smp = [x for x in samples if a <= x[0] < b]
    explore = sum(1 for x in smp if x[3] != x[4])
    phase_rows.append(dict(phase=s, workload=NAME[SEQ[i - 1]], prev=NAME[SEQ[i - 2]] if i > 1 else '',
                           seconds=round(b - a, 1), resets=sum(1 for x in resets if a <= x[0] < b),
                           windows=len(smp), explore_windows=explore,
                           waf_last600=round(target, 4) if target else '',
                           recovery_s=rec if rec is not None else 'not_recovered'))
    if i == 1:
        continue
    for part in range(4):
        rs = within(resets, a, b, part)
        r = dict(phase=s, transition=f'{NAME[SEQ[i - 2]]}->{NAME[SEQ[i - 1]]}', part=part,
                 resets_in_phase=len(rs))
        if rs:
            t_r, _, d = rs[0]
            r['detect_s'] = round(t_r - a, 1)
            r['detect_path'] = 'v6-shift' if (round(t_r, 3), part) in shift_ts or any(abs(t_r - t) < 0.01 and p == part for t, p in shifts) else 'settled-drift'
            after = [x for x in samples if t_r <= x[0] < b and x[1] == part]
            act0 = after[0][2] if after else None
            cov = next((x for x in after[1:] if act0 is not None and x[2] < act0), None)
            r['cover_s_derived'] = round(cov[0] - a, 1) if cov else 'none'
            stl = next((x for x in settles if t_r <= x[0] < b and x[1] == part), None)
            r['settle_s'] = round(stl[0] - a, 1) if stl else 'none'
        else:
            r.update(detect_s='none', detect_path='', cover_s_derived='none', settle_s='none')
        rows.append(r)

OUT.mkdir(exist_ok=True)
for name, data in (('transition_events.csv', rows), ('phase_summary.csv', phase_rows)):
    with open(OUT / name, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(data[0].keys())); w.writeheader(); w.writerows(data)

det = [r['detect_s'] for r in rows if r['detect_s'] != 'none']
by_tr = {}
for r in rows:
    by_tr.setdefault(r['transition'], []).append(r)
summ = dict(source=str(RAW), host='oy-B550M-DS3H (GoCom)', module='nvmev-online-v7.ko sha256 eca51601…',
            transitions=19, partition_transitions=len(rows), detected=len(det),
            detect_s_median=st.median(det) if det else None,
            resets_total=len(resets), v6_shift_resets=len(shifts),
            per_transition_type={k: dict(n=len(v), detected=sum(1 for r in v if r['detect_s'] != 'none'),
                                         detect_s_median=(st.median([r['detect_s'] for r in v if r['detect_s'] != 'none'])
                                                          if any(r['detect_s'] != 'none' for r in v) else None),
                                         settled=sum(1 for r in v if r['settle_s'] != 'none'))
                                 for k, v in sorted(by_tr.items())},
            recovered_phases=sum(1 for p in phase_rows[1:] if p['recovery_s'] != 'not_recovered'))
(OUT / 'summary.json').write_text(json.dumps(summ, indent=1, ensure_ascii=False))
print(json.dumps(summ, indent=1, ensure_ascii=False))
for p in phase_rows:
    print(p)
