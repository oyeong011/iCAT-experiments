#!/usr/bin/env python3
"""Block contaminated data from paper outputs (GoCom, 2026-11-24).

Scans paper-facing outputs for (a) workload labels that exist only in contaminated legacy data and (b) names of runs that
validity.py rejects. Lines that explicitly mark the data as invalid ('무효', 'invalid', '제외', 'INVALID', 'SQLITE_FULL') are
reported as 'flagged-ok'. Everything else is a HIT. Exit status 1 if any HIT -> run this before building the paper PDF.

    python3 -I analysis/final_e1/check_outputs.py [extra files/globs ...]
Output: result/final-e1-validation/output_check.csv (derived)."""
import csv, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validity as V

ROOT = V.ROOT
TARGETS = ['PAPER_KCI_DRAFT.md', 'PAPER_EXPERIMENTS_ONLY.md', 'RESULTS_ALL.md', 'RESULTS_TABLE.md', 'MIX_TABLES.md', 'V4_VS_CAT.md',
           'WRITEUP_DRAFT.md', 'TECHNICAL_SUMMARY.md', 'EXPERIMENTS_OVERVIEW.md', 'INTERVIEW_ONEPAGER.md', 'FIGURE_REVIEW.md', 'ALL_RUNS.csv',
           'figs/data/*.csv', 'figs/data/*.xlsx', 'result/final-20261123/tables/*.csv', 'result/final-20261123/report.md',
           'report/final-e1-validation/tables/*.md', 'report/final-e1-validation/tables/*.csv', 'report/final-e1-validation/figs/*.json']
INVENTORY = {'ALL_RUNS.csv'}
ALLOW_FILE = ROOT / 'result/final-e1-validation/output_check_allow.txt'
ALLOW = [tuple(l.split('#', 1)[0].strip().split('|', 1)) for l in (ALLOW_FILE.read_text().splitlines() if ALLOW_FILE.exists() else [])
         if l.strip() and not l.startswith('#') and '|' in l]
MARK = re.compile(r'무효|invalid|INVALID|제외|SQLITE_FULL|사용 불가')


def invalid_run_names():
    names = set()
    f = ROOT / 'result/final-e1-validation/gocom_detected_invalid.txt'
    if f.exists():
        names |= {l.split()[0].split('/')[-1] for l in f.read_text().splitlines() if l and not l.startswith('#')}
    return names


def lines_of(p):
    if p.suffix == '.xlsx':   # no openpyxl dependency: read every XML part (cells, shared strings, chart titles)
        import zipfile, html
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                if n.endswith('.xml'):
                    txt = html.unescape(re.sub(r'<[^>]+>', ' ', z.read(n).decode('utf-8', 'replace')))
                    for k, seg in enumerate(re.split(r'\s{3,}', txt)):
                        if seg.strip(): yield f'{n}#{k}', seg, None
        return
    rows = p.read_text(errors='replace').splitlines()
    ph_idx = None
    if p.suffix == '.csv' and rows:
        head = next(csv.reader([rows[0].lstrip('\ufeff')]))
        ph_idx = head.index('구간') if '구간' in head else None
    for i, l in enumerate(rows, 1):
        if ph_idx is not None and i > 1:
            cells = next(csv.reader([l]))
            yield str(i), l, (cells[0], cells[ph_idx] if ph_idx < len(cells) else '')
        else:
            yield str(i), l, None


PAPER_SCOPE = ['PAPER_KCI_DRAFT.md', 'PAPER_EXPERIMENTS_ONLY.md', 'report/final-e1-validation/tables/table6_valid.*',
               'report/final-e1-validation/tables/RESULTS_ALL.gated.md', 'report/final-e1-validation/figs/*.json']


def main(extra):
    """--paper: only the manuscript and the files it now cites (final-paper gate). --only: only the given paths."""
    global TARGETS
    if extra and extra[0] == '--only':
        TARGETS, extra = [], extra[1:]
    elif extra and extra[0] == '--paper':
        TARGETS, extra = PAPER_SCOPE, extra[1:]
    runs = invalid_run_names()
    run_re = re.compile(r'\b(' + '|'.join(sorted(map(re.escape, runs), key=len, reverse=True)) + r')\b') if runs else None
    labels = sorted({l for ls in V.CONTAMINATED_LABELS.values() for l in ls}, key=len, reverse=True)
    lab_re = re.compile('|'.join(re.escape(l).replace(r'\ ', r'\s*') for l in labels))
    files = []
    for g in TARGETS + extra:
        if Path(g).is_absolute():
            files += sorted(Path('/').glob(g.lstrip('/'))) if any(c in g for c in '*?[') else [Path(g)]
        else:
            files += sorted(ROOT.glob(g)) if any(c in g for c in '*?[') else [ROOT / g]
    out, hits = [], 0
    for p in files:
        if not p.exists():
            continue
        inventory = p.name in INVENTORY
        for loc, l, lp in lines_of(p):
            what = []
            m = lab_re.search(l)
            if m and V.label_contaminated(l[m.start():]):
                what.append(f'label:{m[0]}')
            if run_re and (m2 := run_re.search(l)):
                what.append(f'run:{m2[0]}')
            if not what:
                continue
            if lp and 'run:' not in ' '.join(what) and V.label_phase_ok(*lp):
                status = 'valid-phase'          # e.g. mixR phase A rows of the trace
            elif any((str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)) == f and sub in l for f, sub in ALLOW):
                status = 'allowed'               # reviewed: valid data (see output_check_allow.txt)
            elif MARK.search(l):
                status = 'flagged-ok'
            elif not re.search(r'\d\.\d{2,}|\d+(\.\d+)?\s*%', l) and 'run:' not in ' '.join(what):
                status = 'label-only'           # label without any value (e.g. a table row of '–' after the gate)
            elif inventory:
                status = 'inventory'            # run inventory, not a paper output: must carry a validity column
            else:
                status = 'HIT'
            hits += status == 'HIT'
            out.append(dict(file=(str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)), where=loc, status=status, match='; '.join(what), text=l.strip()[:220]))
    o = ROOT / 'result/final-e1-validation' / ('output_check_paper.csv' if TARGETS is PAPER_SCOPE else 'output_check.csv')
    with open(o, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['file', 'where', 'status', 'match', 'text']); w.writeheader(); w.writerows(out)
    by = {}
    for r in out:
        by.setdefault((r['file'], r['status']), 0); by[(r['file'], r['status'])] += 1
    for (f, s), n in sorted(by.items()):
        print(f'{s:10s} {n:5d}  {f}')
    print(f'HIT total: {hits}  ->', 'FAIL: contaminated data present' if hits else 'PASS')
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
