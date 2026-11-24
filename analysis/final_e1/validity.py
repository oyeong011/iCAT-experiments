#!/usr/bin/env python3
"""Run/phase validity gate for paper tables and figures (GoCom, 2026-11-24).

A phase is usable only if ALL hold:
  1. exit-code.txt == 0 and summary.txt has the phase;
  2. the run is not listed in INVALID-20261124.txt (SeungCom list; parsed if present) and has no SUSPECT.txt;
  3. no YCSB phase at or before it had failed operations above FAIL_LIMIT (default 1 %).
     A failed YCSB phase changes the device state, so every later phase of that run is also unusable.
     Phases that finished before the first failed YCSB phase (e.g. mixR phase A) stay usable.

Usage from other scripts:
    from validity import usable_phases, run_ok
    run_ok(run_dir)            -> True only if every phase is usable (use for whole-run totals)
    usable_phases(run_dir)     -> set of phase letters that may be used
CLI:  python3 analysis/final_e1/validity.py DIR [DIR ...]
"""
import gzip, re, subprocess, sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FAIL_LIMIT = 0.01
INVALID_LIST_CANDIDATES = ['INVALID-20261124.txt', 'result/INVALID-20261124.txt', 'result/revision-20261123/INVALID-20261124.txt',
                           'result/revision-20261123/mixR/INVALID-20261124.txt', 'result/mix-20260911/INVALID-20261124.txt',
                           'report/revision-20261123/INVALID-20261124.txt']


@lru_cache(maxsize=None)
def invalid_list():
    """Return {run_dir_name_or_path_fragment: set(phases) or None(=all)} from INVALID-20261124.txt, if any copy exists.
    The format is not fixed yet; each non-comment line is read as '<path-or-glob> [phases]'.
    Without explicit phases the entry blocks phases B and C (the contamination reported for mixR)."""
    out = {}
    files = {ROOT / c for c in INVALID_LIST_CANDIDATES} | set(ROOT.glob('result/**/INVALID-2026*.txt'))
    for p in sorted(files):
        if not p.exists():
            continue
        txt = p.read_text(errors='replace')
        # SeungCom's 11-24 file is prose: "every mixR x3 run in this directory is INVALID for phase B, phase C and total WAF"
        m = re.search(r'every (\S+) (?:x\d+ )?runs? in this directory is INVALID for ([^\n.]*)', txt)
        if m:
            phs = set(re.findall(r'phase ([A-Z])\b', m[2])) or {'B', 'C'}
            out[str(p.parent.relative_to(ROOT)) + f'/{m[1]}-*'] = phs
            continue
        for line in txt.splitlines():   # fallback: "<run path> [A,B,...]" lines
            line = line.split('#', 1)[0].strip()
            if not line or not re.match(r'(result/|mix|t4)', line):
                continue
            tok = line.split()
            m2 = re.search(r'\b(?:phases?=)?([A-Z](?:,[A-Z])*)\b', ' '.join(tok[1:]))
            out[tok[0].rstrip('/')] = set(m2[1].split(',')) if m2 else {'B', 'C'}
    return out


def listed(run_dir):
    d = str(Path(run_dir).resolve().relative_to(ROOT)) if Path(run_dir).resolve().is_relative_to(ROOT) else str(run_dir)
    name = Path(run_dir).name
    hit = set()
    for k, ph in invalid_list().items():
        if k == name or d.endswith(k) or Path(d).match(k):
            hit |= ph
    return hit


def _summary_lines(p):
    cmd = ['zgrep', '-a', r'^\[', str(p)] if p.suffix == '.gz' else ['grep', '-a', r'^\[', str(p)]
    return subprocess.run(cmd, capture_output=True, text=True, errors='replace').stdout


@lru_cache(maxsize=None)
def ycsb_status(path):
    """(fail_fraction_worst_op, detail dict, throughput, complete) for one YCSB output file."""
    txt = _summary_lines(Path(path))
    ops = {op: int(n) for op, n in re.findall(r'^\[([A-Z\-]+)\], Operations, (\d+)', txt, re.M)}
    ok = {op: int(n) for op, n in re.findall(r'^\[([A-Z]+)\], Return=OK, (\d+)', txt, re.M)}
    err = {}
    for op, n in re.findall(r'^\[([A-Z]+)\], Return=(?!OK)\w+, (\d+)', txt, re.M):
        err[op] = err.get(op, 0) + int(n)
    det, worst = {}, 0.0
    for op in ops:
        if op.endswith('-FAILED') or op == 'CLEANUP':
            continue
        f = max(ops.get(f'{op}-FAILED', 0), err.get(op, 0)); good = ok.get(op, ops[op]); tot = good + f
        det[op] = (good, f); worst = max(worst, f / tot if tot else 0.0)
    thr = re.search(r'^\[OVERALL\], Throughput\(ops/sec\), ([\d.]+)', txt, re.M)
    return worst, det, float(thr[1]) if thr else None, bool(re.search(r'^\[OVERALL\], RunTime', txt, re.M))


def _ycsb_files_for_phase(d, ph):
    """YCSB output files that belong to phase ph. mix scripts name them ycsb-run.txt / ycsb-run-<ph>.txt (+ ycsb-load)."""
    fs = [f for f in d.glob(f'ycsb-*-{ph}.txt*')]
    if fs:
        return fs + [f for f in d.glob('ycsb-load.txt*')]
    return []


def phase_list(d):
    s = (Path(d) / 'summary.txt')
    if not s.exists():
        return []
    return re.findall(r'^phase([A-Z]|S\d\d)\(([^)]*)\)', s.read_text(), re.M)


@lru_cache(maxsize=None)
def _assess(run_dir):
    d = Path(run_dir)
    reasons = []
    ec = d / 'exit-code.txt'
    if not ec.exists() or ec.read_text().strip() != '0':
        return set(), ['exit-code missing or non-zero']
    if (d / 'SUSPECT.txt').exists():
        return set(), ['SUSPECT.txt present']
    phases = phase_list(d)
    usable, poisoned = set(), False
    blocked = listed(d)
    if blocked:
        reasons.append(f'INVALID-20261124 lists phases {",".join(sorted(blocked))}')
    for ph, kind in phases:
        if not poisoned and ('sqlite' in kind or 'ycsb' in kind):
            fs = _ycsb_files_for_phase(d, ph) or [f for f in d.glob('ycsb-*.txt*')]
            bad = [(f.name, ycsb_status(str(f))) for f in fs]
            bad = [(n, s) for n, s in bad if s[0] > FAIL_LIMIT or not s[3]]
            if bad:
                poisoned = True
                reasons += [f'YCSB {n}: worst op failed {100 * s[0]:.2f}%' + ('' if s[3] else ' (no summary)') for n, s in bad]
        if not poisoned and ph not in blocked:
            usable.add(ph)
        if ph in blocked:
            poisoned = True   # later phases inherit the state of a listed phase
    return usable, reasons


def usable_phases(run_dir):
    return _assess(str(Path(run_dir).resolve()))[0]


def reasons(run_dir):
    return _assess(str(Path(run_dir).resolve()))[1]


def run_ok(run_dir):
    u = usable_phases(run_dir)
    return bool(u) and u == {p for p, _ in phase_list(run_dir)}


if __name__ == '__main__':
    for a in sys.argv[1:]:
        print(a, 'run_ok' if run_ok(a) else 'NOT-ok', 'usable=' + ','.join(sorted(usable_phases(a))) or '-', '|', '; '.join(reasons(a)))


# ---- workload labels of the contaminated legacy data (Sept 2026 mix-20260911, 11-23 revision mixR) ----
# Committed derived files (figs/data/fig14_30s.csv etc.) carry labels, not run paths. Every label below was produced
# only from runs that validity.py rejects (YCSB SQLITE_FULL, or YCSB output missing for mixG).
CONTAMINATED_LABELS = {
    'A': ['FIO-Fast → YCSB-A', '빠른 3영역 → SQLite'],
    'B': ['YCSB-A → FIO-Fast', 'SQLite → 빠른 3영역'],
    'G': ['FIO-Fast ∥ YCSB-A (동시)', '빠른 3영역 + SQLite 동시'],
    'H': ['FIO-Slow → FIO-Fast → YCSB-A', '느린 → 빠른 → SQLite'],
    'J': ['YCSB-A → YCSB-B', 'SQLite 수정 많음 → 읽기 위주'],
    'R': ['FIO-Fast → YCSB-A → FIO-Fast', '빠른 3영역 → SQLite → 빠른 3영역'],
}
RERUN_TAGS = ('재실험', 'rerun', '300k', 'revision-20261124')
_NORM = lambda s: re.sub(r'\s+', '', s)
_BAD = {_NORM(l): k for k, ls in CONTAMINATED_LABELS.items() for l in ls}


def label_contaminated(label):
    """True if a workload label comes from contaminated legacy data. Labels of the 11-24 rerun must carry a RERUN_TAGS
    marker (e.g. 'FIO-Fast → YCSB-A → FIO-Fast (재실험 300k)') to pass."""
    if any(t in label for t in RERUN_TAGS):
        return False
    n = _NORM(label)
    return any(n.startswith(b) for b in _BAD)


def gate_mix(letter, mixdir, pattern):
    """For scripts that read mix{letter}-...: True only if every matching run is fully valid (run_ok)."""
    runs = [p for p in Path(mixdir).glob(pattern.format(m=letter)) if p.is_dir()]
    return bool(runs) and all(run_ok(p) for p in runs)


# phases that stay valid before the failed YCSB phase, per contaminated workload (from validity.usable_phases on the raw runs)
VALID_PREFIX = {'A': 'A', 'B': '', 'G': '', 'H': 'AB', 'J': '', 'R': 'A'}


def label_phase_ok(label, phase):
    """For committed per-phase rows (e.g. fig7_v4_trace.csv '구간' = 'A(FIO-Fast)'): True if the row may be used."""
    if not label_contaminated(label):
        return True
    n = _NORM(label)
    k = next(v for b, v in _BAD.items() if n.startswith(b))
    return bool(phase) and phase[0] in VALID_PREFIX[k]
