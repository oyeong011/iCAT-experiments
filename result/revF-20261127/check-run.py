#!/usr/bin/env python3
"""revF-20261127 post-run check (runs between measurements only). usage: check-run.py <run dir>
Appends one line to checks.tsv. Exit 1 on any anomaly (queue must stop): exit code, missing phases, WAF two paths,
YCSB validity (validity.py), fio errors, kernel BUG/WARNING/Oops, NVMeVirt CPU (cpu1/cpu2 mean busy < 95 % while loaded)."""
import json, re, sys, statistics as st, datetime as dt
from pathlib import Path
sys.path.insert(0, '/home/oy/iCAT-final/analysis/final_e1')
import validity as V
d = Path(sys.argv[1]).resolve(); C = Path('/home/oy/iCAT/result/revF-20261127')
prob, info = [], {}
ec = (d / 'exit-code.txt').read_text().strip() if (d / 'exit-code.txt').exists() else 'missing'
if ec != '0': prob.append(f'exit={ec}')
s = (d / 'summary.txt').read_text() if (d / 'summary.txt').exists() else ''
m = re.search(r'^total .*host_pages=(\d+) gc_pages=(\d+)', s, re.M)
if not m: prob.append('summary total missing')
else:
    h, g = int(m[1]), int(m[2]); info['waf'] = f'{1 + g / h:.6f}'
    fc = (d / 'final-control.txt').read_text() if (d / 'final-control.txt').exists() else ''
    ps = re.findall(r'^part=\d host_pages=(\d+) gc_pages=(\d+)', fc, re.M)
    if (sum(int(a) for a, _ in ps), sum(int(b) for _, b in ps)) != (h, g): prob.append('WAF two paths differ')
for p in 'ABC':
    if not (d / f'phase-{p}-end.txt').exists(): prob.append(f'phase {p} end missing')
    else:
        m2 = re.search(rf'^phase{p}\(\S+\) host_pages=\d+ gc_pages=\d+ WAF=([\d.]+)', s, re.M); info[f'waf_{p}'] = m2[1] if m2 else '?'
for p in 'AC':
    j = d / f'phase-{p}.json'
    if j.exists():
        t = j.read_text(); jj = json.loads(t[t.index('{'):])
        if any(x.get('error', 0) for x in jj.get('jobs', [])): prob.append(f'fio error phase {p}')
if not V.run_ok(d): prob.append('validity: ' + '; '.join(V.reasons(d)))
kl = ''
for f in ('kernel.log', 'kernel-final.log'):
    if (d / f).exists(): kl += (d / f).read_text(errors='replace')
bad = [l for l in kl.splitlines() if re.search(r'BUG:|WARNING:|Oops|Call Trace|general protection|segfault', l)]
if bad: prob.append(f'kernel errors {len(bad)}: {bad[0][:120]}')
# revF: the loaded module must report the pre-registered gamma / C (kernel WATGC_V2 init lines, all 4 partitions)
EXP = {'revF-v4': (65503, 16384), 'revF-g99': (64881, 16384), 'revF-g95': (62259, 16384), 'revF-g90': (58982, 16384),
       'revF-c050': (65503, 32768), 'revF-c075': (65503, 49152)}
pol = re.match(r'mixFYF-(revF-[a-z0-9]+)-rep', d.name)
if pol and pol[1] in EXP:
    own = (d / 'kernel.log').read_text(errors='replace') if (d / 'kernel.log').exists() else ''   # v2: this run's section only (kernel-final.log is the whole dmesg incl. earlier runs)
    got = set(re.findall(r'WATGC_V2 init .*?part=(\d) .*?gamma_q16=(\d+) exploration_q16=(\d+) revA_variant=(\d+)', own))
    gv = {(int(g), int(c), int(v)) for _, g, c, v in got}; parts = {p for p, *_ in got}
    info['init'] = ' '.join(f'{g}/{c}/v{v}' for g, c, v in sorted(gv))
    if gv != {EXP[pol[1]] + (4,)} or parts != {'0', '1', '2', '3'}: prob.append(f'init gamma/C/variant mismatch {sorted(gv)} parts={sorted(parts)}')
# CPU from loadsampler during this run
try:
    t0 = dt.datetime.fromisoformat(open(d / 'environment.txt').readline().strip()).timestamp()   # runner writes date -Is first
    t1 = (d / 'exit-code.txt').stat().st_mtime
    rows = [l.split('\t') for l in (C / 'loadsampler.tsv').read_text().splitlines()[1:]]
    rr = [r for r in rows if t0 <= dt.datetime.fromisoformat(r[0]).timestamp() <= t1 and r[7] == '1']
    if rr:
        c1 = st.mean(float(r[4]) for r in rr); c2 = st.mean(float(r[5]) for r in rr); al = st.mean(float(r[6]) for r in rr); ld = max(float(r[1]) for r in rr)
        info.update(cpu1=f'{c1:.1f}', cpu2=f'{c2:.1f}', all_cpu=f'{al:.1f}', max_load1=f'{ld:.2f}', samples=len(rr))
        if c1 < 95 or c2 < 95: prob.append(f'NVMeVirt CPU low (cpu1 {c1:.1f} %, cpu2 {c2:.1f} %)')
    else: info['samples'] = 0
except Exception as e:
    info['cpu_check'] = f'unavailable ({e.__class__.__name__})'
line = f"{dt.datetime.now().isoformat(timespec='seconds')}\t{d.name}\t{'OK' if not prob else 'ANOMALY'}\t" + ' '.join(f'{k}={v}' for k, v in info.items()) + '\t' + ' | '.join(prob)
import os
with open(os.environ.get('CHECKS_OUT', C / 'checks.tsv'), 'a') as f: f.write(line + '\n')
print(line); sys.exit(1 if prob else 0)
