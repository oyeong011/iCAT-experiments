#!/usr/bin/env python3
"""m1-20261126 run check: check-m1.py <run dir> [<sampler dir>] -> one TSV line (OK/FAIL + metrics) on stdout, exit 0 = OK, 1 = FAIL.
Criteria (pre-registered in preregistration.md): exit 0; module sha256 registered; WAF two paths agree (summary total vs partition sum);
4 partitions in final-control; policy evidence (SmartGC: 4 'smartgc part=' lines; iCAT: WATGC_V2 sample for 4 partitions);
M1PROF when=stop lines with region=GC for 4 partitions; kernel BUG/Oops/Call Trace/soft lockup/hung task = 0; FIO job error = 0 in
every FIO phase; Filebench 'IO Summary' in every Filebench phase; 20 phases present (main) ; CPU1/CPU2 busy >= 95 % (if sampler data).
FIO IOPS below target and the channel-model warning count are recorded, not judged (pre-registered as outcome metrics)."""
import json, re, sys
from pathlib import Path

d = Path(sys.argv[1]); sd = Path(sys.argv[2]) if len(sys.argv) > 2 else None
bad, m = [], {}
rd = lambda p: (d / p).read_text(errors='replace') if (d / p).exists() else ''
if rd('exit-code.txt').strip() != '0': bad.append(f"exit={rd('exit-code.txt').strip() or 'missing'}")
reg = {l.split()[0] for l in (Path(__file__).parent / 'modules.sha256').read_text().splitlines() if l.strip()}
if not any(h in rd('environment.txt') for h in reg): bad.append('module-sha-not-registered')
fc = rd('final-control.txt')
tot = re.search(r'host_pages=(\d+) gc_pages=(\d+)', fc.splitlines()[0]) if fc else None
parts = re.findall(r'^part=(\d) host_pages=(\d+) gc_pages=(\d+) gc_count=(\d+)', fc, re.M)
if not tot or len(parts) != 4: bad.append('final-control')
else:
    h, g = map(int, tot.groups()); hp = sum(int(p[1]) for p in parts); gp = sum(int(p[2]) for p in parts)
    if (h, g) != (hp, gp): bad.append('waf-two-paths')
    m['waf'] = f'{1 + g / h:.6f}'; m['gc_count'] = sum(int(p[3]) for p in parts); m['host_tb'] = f'{h * 4096 / 1e12:.3f}'
    sg = re.findall(r'^smartgc part=\d .*?absorbed=(\d+) evicted=(\d+).*?nand_pages=(\d+)', fc, re.M)
    if 'smartgc' in d.name:
        if len(sg) != 4: bad.append('smartgc-lines')
        else: m['waf_nand'] = f'{sum(int(x[2]) for x in sg) / h:.6f}'
    else: m['waf_nand'] = m['waf']
klog = rd('kernel.log') + rd('kernel-final.log')
if 'icat' in d.name and not all(re.search(rf'WATGC_V2 sample .*part={p} ', klog) for p in range(4)): bad.append('watgc-samples')
prof = re.findall(r'M1PROF when=stop clock=(\S+) part=(\d) region=(\S+) calls=(\d+) ns=(\d+) max_ns=(\d+)', klog)
if {p for _, p, r, *_ in prof if r == 'GC'} != {'0', '1', '2', '3'}: bad.append('m1prof-missing')
for reg_ in ('GC', 'SELECT', 'LEARN'):
    c = sum(int(x[3]) for x in prof if x[2] == reg_); n = sum(int(x[4]) for x in prof if x[2] == reg_)
    if c: m[f'{reg_.lower()}_ns_per_call'] = f'{n / c:.1f}'
nerr = len(re.findall(r'BUG[: ]|Oops|Call Trace|soft lockup|hung_task|blocked for more than', klog))
if nerr: bad.append(f'kernel-errors={nerr}')
m['chmodel_warn_lines'] = klog.count('Need to increase array size')
slots = sorted({p.name.split('-')[1].split('.')[0] for p in d.glob('phase-S*.json')} | {p.stem.split('-')[1] for p in d.glob('filebench-S*.txt')})
m['phases'] = len(slots)
if 'smoke' not in d.name and len(slots) != 20: bad.append(f'phases={len(slots)}')
miss = 0
for j in sorted(d.glob('phase-S*.json')):
    try: jobs = json.loads(j.read_text())['jobs']
    except Exception: bad.append(f'fio-json:{j.name}'); continue
    if any(x['error'] for x in jobs): bad.append(f'fio-error:{j.name}')
    for x in jobs:
        t = float(str(x.get('job options', {}).get('rate_iops', '0')).split(',')[0] or 0)
        if t and x['write']['iops'] < 0.95 * t: miss += 1
m['fio_jobs_below_95pct_of_target'] = miss
for fb in sorted(d.glob('filebench-S*.txt')):
    if 'IO Summary' not in fb.read_text(errors='replace'): bad.append(f'filebench:{fb.name}')
if sd and (sd / 'stat.tsv').exists():
    rows = [l.split('\t', 1)[1].strip('|').split('|') for l in (sd / 'stat.tsv').read_text().splitlines() if '\t' in l]
    if len(rows) >= 2:
        def busy(a, b):
            a, b = list(map(int, a.split()[1:])), list(map(int, b.split()[1:])); dt = sum(b) - sum(a)
            return 100 * (1 - ((b[3] + b[4]) - (a[3] + a[4])) / dt) if dt else 0
        for k, name in ((1, 'cpu1'), (2, 'cpu2')):
            m[name] = f'{busy(rows[0][k], rows[-1][k]):.1f}'
            if float(m[name]) < 95: bad.append(f'{name}-busy<95')
print('\t'.join([d.name, 'FAIL' if bad else 'OK', ' '.join(f'{k}={v}' for k, v in m.items()), ','.join(bad)]))
sys.exit(1 if bad else 0)
