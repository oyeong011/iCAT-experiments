#!/usr/bin/env python3
"""Classify check_outputs.py HITs: manuscript body / manuscript table / paper figure data / legacy outputs.
Output: result/final-e1-validation/output_check_classified.csv (derived)."""
import csv, collections, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; O = ROOT / 'result/final-e1-validation'
MANUSCRIPT = {'PAPER_KCI_DRAFT.md', 'PAPER_EXPERIMENTS_ONLY.md'}
PAPER_FIG_DATA = set()   # the manuscript links only figures.py PNGs; no figs/data file is cited by the manuscript
rows = list(csv.DictReader(open(O / 'output_check.csv')))
out = []
for r in rows:
    if r['status'] != 'HIT': continue
    f = Path(r['file']).name
    if f in MANUSCRIPT:
        cat = 'manuscript-table' if r['text'].lstrip().startswith('|') else 'manuscript-body'
        scope = 'IN-PAPER'
    elif r['file'] in PAPER_FIG_DATA:
        cat, scope = 'paper-figure-data', 'IN-PAPER'
    elif r['file'].startswith('report/final-e1-validation/'):
        cat, scope = 'validation-document', 'NOT-IN-PAPER'
    elif r['file'].startswith('figs/data/'):
        cat, scope = 'legacy-figure-data', 'NOT-IN-PAPER'
    else:
        cat, scope = 'legacy-report', 'NOT-IN-PAPER'
    out.append(dict(scope=scope, category=cat, **r))
with open(O / 'output_check_classified.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
c = collections.Counter((x['scope'], x['category'], x['file']) for x in out)
for k, n in sorted(c.items()): print(n, *k)
print('total', len(out))
