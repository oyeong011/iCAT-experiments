#!/usr/bin/env python3
"""Learning curve of one iCAT run from its kernel.log (WATGC_V2 sample lines).
python3 analysis/learning-curve.py <run dir> [out.png]   -> 5-min bins: window WAF, #distinct arms tried, best-arm changes"""
import re, sys, collections
from pathlib import Path
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
d = Path(sys.argv[1]); out = sys.argv[2] if len(sys.argv) > 2 else str(d / 'learning-curve.png')
rows = []; marks = []
for l in open(d / 'kernel.log', errors='replace'):
    t = re.match(r'\[\s*([\d.]+)\]', l)
    if not t: continue
    t = float(t[1])
    if 'phase=' in l and ('START' in l or 'END' in l) and 'WATGC' not in l: marks.append((t, re.search(r'phase=(\w+) (START|END)', l).groups()))
    if 'WATGC_V2 sample' not in l: continue
    v = dict(re.findall(r'(\w+)=(-?\w+)', l)); rows.append((t, int(v['host']), int(v['gc_pages']), int(v['evaluated']), int(v['best']), v['part']))
t0 = min(t for t, *_ in rows); B = 300
bins = collections.defaultdict(list)
for r in rows: bins[int((r[0] - t0) // B)].append(r)
xs = sorted(bins); waf = []; narm = []; nbest = []
for b in xs:
    g = bins[b]; h = sum(r[1] for r in g); gc = sum(r[2] for r in g)
    waf.append((h + gc) / h); narm.append(len({r[3] for r in g}))
    p0 = [r[4] for r in g if r[5] == '0']; nbest.append(sum(1 for a, c in zip(p0, p0[1:]) if a != c))
fig, ax = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
tm = [(b + 0.5) * B / 60 for b in xs]
ax[0].plot(tm, waf, 'o-'); ax[0].set_ylabel('WAF (5-min bin)'); ax[0].grid(alpha=.3)
ax[1].bar(tm, narm, width=B / 60 * .8); ax[1].set_ylabel('# distinct arms tried'); ax[1].set_ylim(0, 62); ax[1].grid(alpha=.3)
ax[2].bar(tm, nbest, width=B / 60 * .8, color='tab:red'); ax[2].set_ylabel('best-arm changes\n(partition 0)'); ax[2].set_xlabel('minutes since first window'); ax[2].grid(alpha=.3)
for t, (ph, ev) in marks:
    if ev == 'START':
        for a in ax: a.axvline((t - t0) / 60, color='k', ls='--', lw=.8)
        ax[0].text((t - t0) / 60, ax[0].get_ylim()[1], f' phase {ph}', va='top', fontsize=8)
fig.suptitle(f'iCAT learning curve: {d.name}  (total WAF {(sum(r[1] for r in rows)+sum(r[2] for r in rows))/sum(r[1] for r in rows):.3f})')
fig.tight_layout(); fig.savefig(out, dpi=110); print(out)
