#!/usr/bin/env python3
"""revC-20261124 learner metrics from kernel logs (E6/E7 audit). Run AFTER the campaign (reads kernel-snapshots too).
    python3 -I analysis/revision_gocom/revC_learner.py [RAW_DIR]
Only lines after this run's own BEGIN marker are used (dmesg may still hold earlier runs).
Per run (sum or list over 4 partitions):
  windows, selections, evaluations of non-incumbent arms (exploration), eliminations (count of active drops),
  elimination times (s after phase-A start) and window numbers, final best arm per partition, final active count,
  distinct arms evaluated, per-arm evaluation counts, exploration cost (host and GC pages in windows whose evaluated arm != best),
  learner elapsed time (sum of learner_ns, kernel ktime, NOT process CPU), drift resets.
Outputs (derived): result/revC-20261124-analysis/{learner_runs.csv, arm_evals.csv, eliminations.csv}"""
import collections, csv, datetime as dt, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/home/oy/iCAT/result/revC-20261124/raw')
OUT = ROOT / 'result/revC-20261124-analysis'; OUT.mkdir(parents=True, exist_ok=True)
TS = re.compile(r'^\[\s*([\d.]+)\]')
SAMPLE = re.compile(r'WATGC_V2 sample ns=\d+ part=(\d) epoch=(\d+) window=(\d+) .*?evaluated=(\d+) .*?host=(\d+) gc_pages=(\d+) .*?best=(\d+) next=(\d+)(?: settled=(\d))?(?: active=(\d+))?')
SUMMARY = re.compile(r'WATGC_V2 summary ns=\d+ part=(\d) .*?best=(\d+) .*?(?:select=(\d+) eval_explore=(\d+) elim=(\d+) best_change=(\d+) reset=(\d+) learner_ns=(\d+) active=(\d+))?$')


def lines_of(d, tag):
    txt = set()
    for f in [d / 'kernel.log', d / 'kernel-final.log', *sorted((d / 'kernel-snapshots').glob('*.log'))]:
        if f.exists(): txt.update(f.read_text(errors='replace').splitlines())
    L = sorted((float(m[1]), l) for l in txt if (m := TS.match(l)))
    begins = [t for t, l in L if f'mix-mixFYF-{tag}-' in l and l.rstrip().endswith('BEGIN')]
    if not begins: return [], {}
    t0 = max(begins); L = [(t, l) for t, l in L if t >= t0]
    marks = {m[1]: t for t, l in L for m in [re.search(r'phase=(\w) START', l)] if m}
    return L, marks


runs, armrows, elimrows = [], [], []
for d in sorted(RAW.glob('mixFYF-*-rep[0-9]*')):
    if not d.is_dir(): continue
    m = re.match(r'mixFYF-(.+?)-rep(\d)(-smoke120)?$', d.name); pol, rep, smoke = m[1], int(m[2]), bool(m[3])
    L, marks = lines_of(d, pol)
    if not L: continue
    tA = marks.get('A', L[0][0])
    prev_active = {}; evals = collections.Counter(); per_part_evals = collections.defaultdict(collections.Counter)
    expl_host = expl_gc = all_host = 0; windows = 0; summ = {}
    for t, l in L:
        s = SAMPLE.search(l)
        if s:
            part, ep, win, ev, host, gc, best, nxt = map(int, s.groups()[:8]); act = int(s[10]) if s[10] else None
            windows += 1; evals[ev] += 1; per_part_evals[part][ev] += 1; all_host += host
            if ev != best: expl_host += host; expl_gc += gc
            if act is not None and part in prev_active and prev_active[part] is not None and act < prev_active[part]:
                elimrows.append(dict(run=d.name, policy=pol, rep=rep, part=part, window=win, t_s=round(t - tA, 1),
                                     phase=max((p for p in 'ABC' if p in marks and marks[p] <= t), default='?'),
                                     active_before=prev_active[part], active_after=act, best=best))
            prev_active[part] = act
            continue
        u = SUMMARY.search(l.rstrip())
        if u: summ[int(u[1])] = u.groups()   # last summary per partition wins
    finals = {p: (int(g[1]), *(int(x) if x else None for x in g[2:])) for p, g in summ.items()}
    lns = [f[6] for f in finals.values() if f[6] is not None]
    runs.append(dict(run=d.name, policy=pol, rep=rep, smoke=smoke, windows=windows, distinct_arms_evaluated=len(evals),
                     eliminations=sum(1 for e in elimrows if e['run'] == d.name),
                     elim_events_counter=sum(f[3] for f in finals.values() if f[3] is not None) if lns else '',
                     selections=sum(f[1] for f in finals.values() if f[1] is not None) if lns else '',
                     eval_explore=sum(f[2] for f in finals.values() if f[2] is not None) if lns else '',
                     best_changes=sum(f[4] for f in finals.values() if f[4] is not None) if lns else '',
                     resets=sum(f[5] for f in finals.values() if f[5] is not None) if lns else '',
                     final_best_arms=' '.join(str(finals[p][0]) for p in sorted(finals)),
                     final_active=' '.join(str(prev_active.get(p, '')) for p in sorted(prev_active)),
                     explore_host_pages=expl_host, explore_gc_pages=expl_gc, window_host_pages=all_host,
                     explore_host_share=f'{expl_host / all_host:.4f}' if all_host else '',
                     learner_elapsed_ms=f'{sum(lns) / 1e6:.4f}' if lns else 'n/a (no learner_ns in this module)'))
    for a, n in sorted(evals.items()):
        armrows.append(dict(run=d.name, policy=pol, rep=rep, arm=a, k_index=a // 15, evaluations=n))
for name, rows in (('learner_runs.csv', runs), ('arm_evals.csv', armrows), ('eliminations.csv', elimrows)):
    if rows:
        with open(OUT / name, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in runs:
    print(r['run'], 'win', r['windows'], 'arms', r['distinct_arms_evaluated'], 'elim', r['eliminations'], '/', r['elim_events_counter'],
          'best', r['final_best_arms'], 'active', r['final_active'], 'explore_host_share', r['explore_host_share'], 'learner_ms', r['learner_elapsed_ms'])
