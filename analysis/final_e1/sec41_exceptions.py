#!/usr/bin/env python3
"""Raw per-run evidence for the four 4.1 exceptions (GoCom, 2026-11-24).
Re-uses analysis/summary.py's own aggregation (executed with the worktree's result path) so the numbers are the
ones behind RESULTS_ALL §1/§4. Output: report/final-e1-validation/tables/sec41_exceptions.csv (derived)."""
import csv, io, contextlib, statistics as st, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
src = (ROOT / 'analysis/summary.py').read_text().replace("Path('/home/oy/iCAT/result')", f"Path('{ROOT}/result')")
ns = {'__name__': 'summary_exec'}; sys.argv = ['summary.py']
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src, 'summary.py', 'exec'), ns)
rows = ns['rows']   # (group, workload, policy, waf, host)
CASES = [('Varmail 단독 (filebench, 5분)', 'filebench', 'varmail', ('gh-online', 'gh-greedy', 'gh-cat37', 'fixed47', 'fixed50', 'fixed10')),
         ('SQLite 읽기95/수정5 단독', 'sqlite', 'b', ('gh-online', 'gh-cat37', 'gh-greedy', 'fixed47', 'fixed50', 'fixed10')),
         ('OLTP → Varmail 1배 (mixO)', 'mix:mixO', None, ('online', 'fixed37', 'greedy', 'fixed47', 'fixed50', 'fixed10')),
         ('YCSB-A → OLTP 1배 (mixP)', 'mix:mixP', None, ('online', 'fixed37', 'greedy', 'fixed47', 'fixed50', 'fixed10'))]
out = []
for label, g, w, pols in CASES:
    for wl in sorted({r[1] for r in rows if r[0] == g and (w is None or r[1] == w)}):
        for p in pols:
            v = [(r[3], r[4]) for r in rows if r[0] == g and r[1] == wl and r[2] == p]
            if not v: continue
            ws = [x for x, _ in v]
            out.append(dict(case=label, group=g, measure=wl, policy=p, n=len(ws), mean=f'{st.mean(ws):.4f}', sd=f'{st.stdev(ws):.4f}' if len(ws) > 1 else '',
                            min=f'{min(ws):.4f}', max=f'{max(ws):.4f}', runs=' '.join(f'{x:.4f}' for x in ws),
                            host_pages=' '.join(str(h) for _, h in v)))
o = ROOT / 'report/final-e1-validation/tables/sec41_exceptions.csv'
with open(o, 'w', newline='') as f:
    wr = csv.DictWriter(f, fieldnames=list(out[0])); wr.writeheader(); wr.writerows(out)
for r in out: print(r['case'][:22].ljust(22), r['measure'][:18].ljust(18), r['policy'].ljust(10), r['n'], r['mean'], r['sd'], r['runs'])
