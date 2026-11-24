#!/usr/bin/env python3
"""Scan every run directory under result/ that has YCSB output; report per-operation success.
A YCSB phase is INVALID if any op type has FAILED > 1 % of (OK + FAILED) operations.
Output: result/final-e1-validation/ycsb_validity_all.csv (new file)."""
import csv, gzip, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / 'result/final-e1-validation'; OUT.mkdir(parents=True, exist_ok=True)
THRESH = 0.01

def read(p):
    # YCSB summary lines start with '[' (10 s status lines start with a date): keep only those
    import subprocess
    cmd = ['zgrep', '-a', r'^\[', str(p)] if p.suffix == '.gz' else ['grep', '-a', r'^\[', str(p)]
    return subprocess.run(cmd, capture_output=True, text=True, errors='replace').stdout

def parse(txt):
    ops = {}
    for op, n in re.findall(r'^\[([A-Z\-]+)\], Operations, (\d+)', txt, re.M):
        ops[op] = int(n)
    ok = {op: int(n) for op, n in re.findall(r'^\[([A-Z]+)\], Return=OK, (\d+)', txt, re.M)}
    err = {}
    for op, rc, n in re.findall(r'^\[([A-Z]+)\], Return=(?!OK)(\w+), (\d+)', txt, re.M):
        err[op] = err.get(op, 0) + int(n)
    thr = re.search(r'^\[OVERALL\], Throughput\(ops/sec\), ([\d.]+)', txt, re.M)
    rt = re.search(r'^\[OVERALL\], RunTime\(ms\), (\d+)', txt, re.M)
    return ops, ok, err, float(thr[1]) if thr else None, int(rt[1]) if rt else None

def check(path):
    ops, ok, err, thr, rt = parse(read(path))
    rows = []
    worst = 0.0
    for op in sorted(k for k in ops if not k.endswith('-FAILED') and k not in ('CLEANUP',)):
        failed = max(ops.get(f'{op}-FAILED', 0), err.get(op, 0))  # same failures appear in both lines
        total = ok.get(op, ops[op]) + failed
        frac = failed / total if total else 0.0
        worst = max(worst, frac)
        rows.append((op, ok.get(op, ops[op]), failed, frac))
    complete = rt is not None
    return rows, worst, thr, rt, complete

if __name__ == '__main__':
    out = []
    files = sorted(set(ROOT.glob('result/**/ycsb-*.txt.gz')) | set(ROOT.glob('result/**/ycsb-*.txt')))
    files = [f for f in files if not f.name.startswith('ycsb-check')]
    for f in files:
        name = f.name.replace('.gz', '').replace('.txt', '')
        try:
            rows, worst, thr, rt, complete = check(f)
        except Exception as e:
            out.append(dict(dir=str(f.parent.relative_to(ROOT)), file=name, status=f'PARSE-ERROR {e}')); continue
        detail = '; '.join(f'{op} ok={o} failed={x} ({100*fr:.2f}%)' for op, o, x, fr in rows)
        status = 'NO-SUMMARY' if not complete else ('INVALID' if worst > THRESH else 'OK')
        out.append(dict(dir=str(f.parent.relative_to(ROOT)), file=name, status=status, worst_fail_pct=f'{100*worst:.3f}',
                        throughput_ops_s=f'{thr:.1f}' if thr else '', runtime_s=f'{rt/1000:.0f}' if rt else '', detail=detail))
    keys = ['dir', 'file', 'status', 'worst_fail_pct', 'throughput_ops_s', 'runtime_s', 'detail']
    with open(OUT / 'ycsb_validity_all.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction='ignore'); w.writeheader(); w.writerows(out)
    from collections import Counter
    print(Counter(r['status'] for r in out))
