#!/usr/bin/env python3
"""Re-check (from raw files) the data sets the revision relies on (GoCom, 2026-11-24):
  (4) GoCom revA / revB mixFYF runs: exit code, YCSB load/run operation counts and success, fio phase completion,
      WAF two paths; then recompute Random-vs-V4 and the ablation effects from validity-passed runs only.
  (5) SmartGC comparison (mixY, plus smoke/fitcheck runs): YCSB use, exit code, every phase present and complete
      (fio json error=0, filebench IO Summary, phase end marker), WAF two paths, NAND formula.
Outputs (derived): result/final-e1-validation/recheck_{gocom_mixfyf,smartgc_runs,gocom_effects}.csv"""
import csv, json, math, re, statistics as st, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validity as V
ROOT = V.ROOT; OUT = ROOT / 'result/final-e1-validation'
T95 = {2: 4.303, 3: 3.182, 4: 2.776}


def total(d):
    m = re.search(r'^total .*host_pages=(\d+) gc_pages=(\d+)', (d / 'summary.txt').read_text(), re.M)
    return (int(m[1]), int(m[2])) if m else (0, 0)


def partsum(d):
    t = (d / 'final-control.txt').read_text() if (d / 'final-control.txt').exists() else ''
    ps = re.findall(r'^part=\d host_pages=(\d+) gc_pages=(\d+)', t, re.M)
    return sum(int(a) for a, _ in ps), sum(int(b) for _, b in ps)


def fio_ok(f):
    try:
        j = json.loads(f.read_text()[f.read_text().index('{'):])
        return all(job.get('error', 0) == 0 for job in j.get('jobs', []))
    except Exception:
        return None


def phase_checks(d):
    """per phase: kind, start/end marker present, fio json error-free / filebench summary present / YCSB success."""
    out = []
    pl = V.phase_list(d)
    aliases = any(p.startswith('S') for p, _ in pl)   # mixY: phaseA/phaseB in summary.txt are copies of S01/S02
    for p, kind in pl:
        if aliases and len(p) == 1: continue
        end = (d / f'phase-{p}-end.txt').exists() or (d / f'phase-{p}-end.time').exists()
        detail = ''
        if 'test' in kind or 'fio' in kind:
            j = d / f'phase-{p}.json'
            detail = 'fio:' + ('ok' if j.exists() and fio_ok(j) else ('json-missing' if not j.exists() else 'ERROR'))
        elif 'varmail' in kind or 'oltp' in kind or 'filebench' in kind:
            fb = d / f'filebench-{p}.txt'
            detail = 'filebench:' + ('ok' if fb.exists() and 'IO Summary' in fb.read_text(errors='replace') else 'MISSING')
        elif 'sqlite' in kind or 'ycsb' in kind:
            fs = sorted(d.glob(f'ycsb-run-{p}.txt*')) or sorted(d.glob('ycsb-run.txt*'))
            s = V.ycsb_status(str(fs[0])) if fs else None
            detail = 'ycsb:' + (f'worst_fail={100 * s[0]:.3f}% complete={s[3]}' if s else 'MISSING')
        out.append((p, kind, end, detail))
    return out


def ycsb_counts(d):
    r = {}
    for name in ('ycsb-load', 'ycsb-run-B', 'ycsb-run'):
        fs = sorted(d.glob(f'{name}.txt*'))
        if not fs: continue
        w, det, thr, done = V.ycsb_status(str(fs[0]))
        r[name] = (det, w, done, thr)
    return r


# ---------------- (4) GoCom mixFYF ----------------
rows = []
for d in sorted(list((ROOT / 'result/revA-20261114/raw').glob('mixFYF-*')) + list((ROOT / 'result/revB-20261122/raw').glob('mixFYF-*'))):
    if not d.is_dir() or not (d / 'summary.txt').exists(): continue
    h, g = total(d); ph, pg = partsum(d); yc = ycsb_counts(d)
    load = yc.get('ycsb-load', ({}, 0, False, None)); run = yc.get('ycsb-run-B') or yc.get('ycsb-run') or ({}, 0, False, None)
    pcs = phase_checks(d)
    rows.append(dict(set=d.parent.parent.name, run=d.name, exit=(d / 'exit-code.txt').read_text().strip() if (d / 'exit-code.txt').exists() else 'missing',
                     run_ok=V.run_ok(d), ycsb_load_insert_ok=load[0].get('INSERT', ('', ''))[0], ycsb_load_failed=load[0].get('INSERT', ('', ''))[1],
                     ycsb_read_ok=run[0].get('READ', ('', ''))[0], ycsb_read_failed=run[0].get('READ', ('', ''))[1],
                     ycsb_update_ok=run[0].get('UPDATE', ('', ''))[0], ycsb_update_failed=run[0].get('UPDATE', ('', ''))[1],
                     ycsb_worst_fail_pct=f'{100 * run[1]:.4f}', ycsb_complete=run[2], ycsb_ops_s=f'{run[3]:.1f}' if run[3] else '',
                     phases=' '.join(f'{p}:{k}:{"end" if e else "NO-END"}:{x}' for p, k, e, x in pcs),
                     waf_summary=f'{1 + g / h:.6f}' if h else '', waf_partitions=f'{1 + pg / ph:.6f}' if ph else '',
                     two_paths_equal=(h, g) == (ph, pg)))
with open(OUT / 'recheck_gocom_mixfyf.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

# effects from validity-passed runs only
def grp(prefix):
    return [float(r['waf_summary']) for r in rows if r['run'].startswith(prefix) and re.search(r'-rep\d$', r['run']) and r['run_ok']]
def welch(a, b):
    ma, mb = st.mean(a), st.mean(b); va, vb = st.variance(a) / len(a), st.variance(b) / len(b); se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)); q = T95[min(T95, key=lambda k: abs(k - df))]
    return ma - mb, ma - mb - q * se, ma - mb + q * se, df
eff = []
v4 = grp('mixFYF-revA-v4-')
for name, pre, base in [('Random − V4', 'mixFYF-revA-random-', v4), ('revA-V1 (no drift) − V4', 'mixFYF-revA-v1-', v4),
                        ('revA-V2 (no elim, no settle) − V4', 'mixFYF-revA-v2-', v4), ('noelim − V4', 'mixFYF-revB-noelim-', v4),
                        ('nosettle − V4', 'mixFYF-revB-nosettle-', v4)]:
    a = grp(pre)
    if len(a) >= 2 and len(base) >= 2:
        dlt, lo, hi, df = welch(a, base)
        eff.append(dict(effect=name, n=len(a), n_v4=len(base), mean=f'{st.mean(a):.4f}', v4_mean=f'{st.mean(base):.4f}', diff=f'{dlt:+.4f}',
                        ci95=f'[{lo:+.4f}, {hi:+.4f}]', df=f'{df:.1f}', excludes_zero=lo > 0 or hi < 0))
    else:
        eff.append(dict(effect=name, n=len(a), n_v4=len(base), mean=f'{st.mean(a):.4f}' if a else '', v4_mean='', diff='', ci95='n<2', df='', excludes_zero=''))
with open(OUT / 'recheck_gocom_effects.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(eff[0])); w.writeheader(); w.writerows(eff)

# ---------------- (5) SmartGC comparison ----------------
sg = []
cands = [d for g in ('result/gc-20261010/*', 'result/gocom-sg-20261119/*', 'result/smartgc-20261119/resume/*', 'result/revision-20261123/check-fixed47-nov/*')
         for d in ROOT.glob(g) if d.is_dir() and (d / 'summary.txt').exists()]
for d in sorted(cands):
    pl = V.phase_list(d); uses_ycsb = any('sqlite' in k or 'ycsb' in k for _, k in pl)
    ycsb_bytes = sum(len(V._summary_lines(f)) for f in d.glob('ycsb-*.txt*'))
    pcs = phase_checks(d)
    h, g = total(d); ph, pg = partsum(d)
    fc = (d / 'final-control.txt').read_text() if (d / 'final-control.txt').exists() else ''
    hp = {int(a): (int(b), int(c)) for a, b, c in re.findall(r'^part=(\d+) host_pages=(\d+) gc_pages=(\d+)', fc, re.M)}
    sgp = re.findall(r'smartgc part=(\d+) .*?absorbed=(\d+) evicted=(\d+) .*?nand_pages=(\d+)', fc)
    nand_ok = all(int(n) == hp[int(pt)][0] - int(ab) + int(ev) + hp[int(pt)][1] for pt, ab, ev, n in sgp) if sgp else 'n/a (no GC buffer)'
    bad_phase = [f'{p}:{x}' for p, k, e, x in pcs if not e or 'ERROR' in x or 'MISSING' in x or 'missing' in x]
    sg.append(dict(run=str(d.relative_to(ROOT)), exit=(d / 'exit-code.txt').read_text().strip() if (d / 'exit-code.txt').exists() else 'missing',
                   n_phases=len(pl), uses_ycsb=uses_ycsb, ycsb_summary_bytes=ycsb_bytes, run_ok=V.run_ok(d), incomplete_phases=' '.join(bad_phase),
                   waf_summary=f'{1 + g / h:.6f}' if h else '', two_paths_equal=(h, g) == (ph, pg) if ph else '',
                   smartgc_nand_formula_ok=nand_ok, reasons=' | '.join(V.reasons(d))))
with open(OUT / 'recheck_smartgc_runs.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(sg[0])); w.writeheader(); w.writerows(sg)

print('== mixFYF runs', len(rows), 'run_ok', sum(r['run_ok'] for r in rows), 'two_paths_equal', sum(r['two_paths_equal'] for r in rows),
      'max ycsb fail %', max(float(r['ycsb_worst_fail_pct']) for r in rows))
print('   load insert ok values', sorted({r['ycsb_load_insert_ok'] for r in rows}), 'read+update ops', sorted({(int(r['ycsb_read_ok'] or 0) + int(r['ycsb_update_ok'] or 0)) for r in rows}))
print('   phases with problems:', [r['run'] for r in rows if 'NO-END' in r['phases'] or 'ERROR' in r['phases'] or 'MISSING' in r['phases']])
for e in eff: print('  ', e)
print('== SmartGC-comparison runs')
for r in sg: print('  ', r['run'], 'exit', r['exit'], 'phases', r['n_phases'], 'ycsb', r['uses_ycsb'], r['ycsb_summary_bytes'], 'ok', r['run_ok'],
                   'incomplete', r['incomplete_phases'] or '-', 'WAF', r['waf_summary'], '2path', r['two_paths_equal'], 'nand', r['smartgc_nand_formula_ok'])

# ---------------- (7) single-workload SQLite (YCSB) runs: YCSB output is inline in result/sqlite/*.console.txt ----------------
sq = []
for f in sorted((ROOT / 'result/sqlite').glob('*.console.txt')):
    t = f.read_text(errors='replace')
    ops, ok, bad = {}, {}, {}
    for op, n in re.findall(r'^\[([A-Z\-]+)\], Operations, (\d+)', t, re.M): ops[op] = ops.get(op, 0) + int(n)
    for op, n in re.findall(r'^\[([A-Z]+)\], Return=OK, (\d+)', t, re.M): ok[op] = ok.get(op, 0) + int(n)
    for op, n in re.findall(r'^\[([A-Z]+)\], Return=(?!OK)\w+, (\d+)', t, re.M): bad[op] = bad.get(op, 0) + int(n)
    worst = 0.0
    for op in ops:
        if op.endswith('-FAILED') or op == 'CLEANUP': continue
        fl = max(ops.get(op + '-FAILED', 0), bad.get(op, 0)); tot = ok.get(op, ops[op]) + fl
        worst = max(worst, fl / tot if tot else 0.0)
    w = re.search(r'^\[WAF\] module=\S+ WAF=([\d.]+)', t, re.M)
    sq.append(dict(run=f.name, ycsb_summary=bool(ops), worst_fail_pct=f'{100 * worst:.4f}', sqlite_full='SQLITE_FULL' in t,
                   waf=w[1] if w else '', status='no-ycsb-summary' if not ops else ('INVALID' if worst > V.FAIL_LIMIT or 'SQLITE_FULL' in t else 'OK')))
with open(OUT / 'recheck_sqlite_single.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(sq[0])); w.writeheader(); w.writerows(sq)
import collections as _c
print('== SQLite single-workload consoles', dict(_c.Counter(r['status'] for r in sq)), 'max fail %', max(float(r['worst_fail_pct']) for r in sq if r['ycsb_summary']))
