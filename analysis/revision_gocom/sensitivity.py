#!/usr/bin/env python3
"""GoCom revision 2026-11-23: parameter-sensitivity evidence that can be extracted from EXISTING mixFYF logs.

Nothing is re-run. Inputs: result/revA-20261114/raw, result/revB-20261122/raw (GoCom, mixFYF).
Outputs: result/revision-gocom-20261123/{window_noise.csv, elim_replay.csv, gamma_weight.csv, settle_probe.csv}

All outputs are COMPUTED from logged per-window rewards (WATGC_V2 sample lines: evaluated arm, host, gc_pages,
waf_q16 = 1 + gc/host of that window).  Replays are offline what-ifs on logged rewards; they do not show what WAF
the device would have reached with another parameter value.
"""
import csv, math, re, statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'result/revision-gocom-20261123'; OUT.mkdir(parents=True, exist_ok=True)
RUNS = sorted((ROOT / 'result/revA-20261114/raw').glob('mixFYF-revA-*-rep[0-9]')) + \
       sorted((ROOT / 'result/revB-20261122/raw').glob('mixFYF-revB-*-rep[0-9]'))
GAMMA = 65503 / 65536


def parse(d):
    marks, smp = {}, []
    for l in (d / 'kernel.log').read_text(errors='replace').splitlines():
        m = re.match(r'\[\s*([\d.]+)\]', l)
        if not m: continue
        t = float(m[1])
        p = re.search(r'mix-mixFYF\S* phase=([ABC]) (START|END)', l)
        if p: marks[(p[1], p[2])] = t; continue
        if 'WATGC_V2 sample' in l:
            kv = dict(re.findall(r'(\w+)=(\S+)', l))
            smp.append(dict(t=t, part=int(kv['part']), win=int(kv['window']), arm=int(kv['evaluated']), best=int(kv['best']),
                            host=int(kv['host']), gc=int(kv['gc_pages']), waf=int(kv['waf_q16']) / 65536,
                            settled=int(kv['settled']), active=int(kv['active']), reset=int(kv['reset'])))
    for s in smp:
        s['phase'] = next((ph for ph in 'ABC' if marks.get((ph, 'START'), 1e18) <= s['t'] < marks.get((ph, 'END'), -1)), None)
    return smp


def policy(d):
    return re.match(r'mixFYF-(.+)-rep\d', d.name)[1]


data = {d.name: (policy(d), parse(d)) for d in RUNS}

# ---- S1. window noise vs window length (incumbent-only stretches of settled learners)
rows = []
for name, (pol, smp) in data.items():
    if pol not in ('revA-v4', 'revB-v4', 'revA-v1', 'revB-arm60', 'revB-noelim'): continue
    for ph in 'AC':
        for part in range(4):
            seq = [s for s in smp if s['part'] == part and s['phase'] == ph]
            # runs of consecutive windows on the same arm while settled
            runs_, cur = [], []
            for s in seq:
                if s['settled'] and s['arm'] == s['best'] and cur and cur[-1]['arm'] == s['arm'] and s['win'] == cur[-1]['win'] + 1:
                    cur.append(s)
                else:
                    if len(cur) >= 2: runs_.append(cur)
                    cur = [s] if s['settled'] and s['arm'] == s['best'] else []
            if len(cur) >= 2: runs_.append(cur)
            for m in (1, 2, 4, 8):
                diffs = []
                for r in runs_:
                    agg = [r[i:i + m] for i in range(0, len(r) - m + 1, m)]
                    w = [1 + sum(x['gc'] for x in a) / sum(x['host'] for x in a) for a in agg]
                    diffs += [(w[i + 1] - w[i]) / ((w[i + 1] + w[i]) / 2) for i in range(len(w) - 1)]
                if len(diffs) >= 3:
                    rows.append((name, pol, ph, part, m, 128 * m, len(diffs), st.stdev(diffs) / math.sqrt(2)))
with open(OUT / 'window_noise.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['run', 'policy', 'phase', 'part', 'aggregate_windows', 'window_gc_equiv', 'n_pairs', 'rel_noise_sd'])
    w.writerows(rows)
noise = {}
for r in rows: noise.setdefault((r[2], r[4]), []).append((r[6], r[7]))
noise_sum = []
for (ph, m), v in sorted(noise.items()):
    tot = sum(n for n, _ in v); pooled = math.sqrt(sum(n * s * s for n, s in v) / tot)
    noise_sum.append((ph, m, 128 * m, len(v), tot, pooled, st.median(s for _, s in v)))
with open(OUT / 'window_noise_summary.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['phase', 'aggregate_windows', 'window_gc_equiv', 'series', 'pairs', 'pooled_rel_sd', 'median_rel_sd'])
    w.writerows(noise_sum)

# ---- S2. elimination threshold replay at first coverage (single-window reward per arm, as V4 sees it)
er = []
for name, (pol, smp) in data.items():
    if pol not in ('revA-v4', 'revB-v4', 'revB-noelim', 'revB-nosettle', 'revA-v2', 'revA-v1'): continue
    for part in range(4):
        seq = [s for s in smp if s['part'] == part and s['phase'] == 'A']
        seen = {}
        for s in seq:
            if s['arm'] not in seen: seen[s['arm']] = s['waf']
            if len(seen) >= 45: break
        if len(seen) < 45: continue
        bestw = min(seen.values())
        # reference arm = arm this partition used most in the 2nd half of phase A (v4-family settled choice; data-driven)
        tail = [s['arm'] for s in seq[len(seq) // 2:]]
        ref = max(set(tail), key=tail.count)
        for th in (0.05, 0.10, 0.15, 0.25, 0.50):
            surv = [a for a, v in seen.items() if v <= bestw * (1 + th)]
            er.append((name, pol, part, th, len(surv), int(ref in surv), ref, int(47 in surv), round(seen.get(47, float('nan')) / bestw - 1, 4)))
with open(OUT / 'elim_replay.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['run', 'policy', 'part', 'threshold', 'survivors_of_45', 'ref_arm_survives', 'ref_arm',
                                   'arm47_survives', 'arm47_gap_to_sweep_best'])
    w.writerows(er)
es = []
# ref-arm survival is only unbiased for learners that never eliminate (noelim, V2): in the others the later
# choice is itself constrained by the 15 % rule (circular).  arm 47 (best of the CAT sweeps) is an outside reference.
for grp, pols in (('no-elimination runs (noelim, V2)', ('revB-noelim', 'revA-v2')), ('all runs', None)):
    for th in (0.05, 0.10, 0.15, 0.25, 0.50):
        x = [r for r in er if r[3] == th and (pols is None or r[1] in pols)]
        es.append((grp, th, len(x), st.mean(r[4] for r in x), min(r[4] for r in x),
                   sum(r[5] for r in x) / len(x) if pols else 'n/a (circular)', sum(r[7] for r in x) / len(x)))
with open(OUT / 'elim_replay_summary.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['group', 'threshold', 'partition_sweeps', 'mean_survivors', 'min_survivors', 'ref_arm_survival_rate', 'arm47_survival_rate'])
    w.writerows(es)

# ---- S3. discount factor: weight left on the oldest observation at the end of each phase (computed)
gw = []
for name, (pol, smp) in data.items():
    if pol not in ('revA-v4', 'revB-v4'): continue
    for part in range(4):
        n = sum(1 for s in smp if s['part'] == part)
        gw.append((name, 'whole run (A+B+C)', part, n, GAMMA ** n))
with open(OUT / 'gamma_weight.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['run', 'span', 'part', 'windows', 'gamma_pow_windows'])
    w.writerows(gw)

# ---- S4. settling time and probe share (V4 family, measured from logs)
sp = []
for name, (pol, smp) in data.items():
    if pol not in ('revA-v4', 'revB-v4', 'revB-noelim', 'revB-arm60', 'revA-v1'): continue
    for ph in 'ABC':
        for part in range(4):
            seq = [s for s in smp if s['part'] == part and s['phase'] == ph]
            if not seq: continue
            first_settle = next((s for s in seq if s['settled']), None)
            sett = [s for s in seq if s['settled']]
            probes = sum(1 for s in sett if s['arm'] != s['best'])
            sp.append((name, pol, ph, part, len(seq), (first_settle['t'] - seq[0]['t']) if first_settle else None,
                       len(sett), probes, probes / len(sett) if sett else None))
with open(OUT / 'settle_probe.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['run', 'policy', 'phase', 'part', 'windows', 'first_settled_after_s', 'settled_windows', 'probe_windows', 'probe_share'])
    w.writerows(sp)
print('noise', noise_sum)
for e in es: print('elim', e)
print('gamma min weight', min(x[4] for x in gw), 'max windows', max(x[3] for x in gw))
for pol in ('revA-v4', 'revB-noelim', 'revA-v1', 'revB-arm60'):
    for ph in 'ABC':
        x = [r for r in sp if r[1] == pol and r[2] == ph]
        fs = [r[5] for r in x if r[5] is not None]
        print(pol, ph, 'settled parts', len(fs), '/', len(x), 'median first settle s', st.median(fs) if fs else None,
              'probe share', round(st.mean(r[8] for r in x if r[8] is not None), 3) if any(r[8] is not None for r in x) else None)
