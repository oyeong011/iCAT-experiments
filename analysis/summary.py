#!/usr/bin/env python3
"""Aggregate every completed run into one table: workload x policy -> mean WAF (n).  python3 analysis/summary.py [-v]"""
import re, glob, statistics as st, sys, collections
from pathlib import Path
R = Path('/home/oy/iCAT/result')
POL = ['gh-greedy', 'greedy', 'fixed10', 'gh-cat37', 'fixed37', 'fixed47', 'fixed50', 'gh-online', 'online']
GC = re.compile(r'GC stats: .*?policy=(\S+) host_pages=(\d+) gc_pages=(\d+)')
rows = []  # (group, workload, policy, waf, host)
def add(g, w, p, waf, host): rows.append((g, w, p, float(waf), int(host)))
# GitHub-method fio: console -> [RESULT] dmesg path
for c in glob.glob(str(R / 'gh-repro-20260914' / '*.console.txt')):
    m = re.match(r'(test\d(?:-s\d)?)-(gh-greedy|gh-cat37|gh-online|fixed\d+)(?:-rep\d)?\.console\.txt', Path(c).name)
    if not m: continue
    res = re.search(r'^\[RESULT\] (\S+)', Path(c).read_text(errors='replace'), re.M)
    if not res or not Path(res[1]).exists(): continue
    g = GC.findall(Path(res[1]).read_text(errors='replace'))
    if g: add('fio(gh)', m[1].split('-')[0], m[2], (int(g[-1][1]) + int(g[-1][2])) / int(g[-1][1]), g[-1][1])
# GitHub-method filebench / sqlite / rocksdb: console -> [WAF] line
for sub, gname in (('filebench', 'filebench'), ('sqlite', 'sqlite'), ('rocksdb', 'rocksdb')):
    for c in glob.glob(str(R / sub / '*.console.txt')):
        m = re.match(r'([a-z]+)-(gh-greedy|gh-cat37|gh-online|fixed\d+)(?:-rep\d)?\.console\.txt', Path(c).name)
        if not m or m[1] == 'smoke': continue
        w = re.search(r'^\[WAF\] module=\S+ WAF=([\d.]+) host_pages=(\d+)', Path(c).read_text(errors='replace'), re.M)
        if w and float(w[1]) > 0: add(gname, m[1], m[2], w[1], w[2])
# start/stop measurement runs (mix-20260911): summary.txt
for s in glob.glob(str(R / 'mix-20260911' / '*' / 'summary.txt')):
    d = Path(s).parent.name
    m = re.match(r'(smoke|main|long|t4|mixA|mixB|mixC)-(fixed\d+|greedy|online)(?:-rep\d)?(-smoke)?$', d)
    if not m or m[1] == 'smoke' or m[3]: continue
    txt = Path(s).read_text()
    for line in txt.splitlines():
        mm = re.match(r'(total|phaseA\(\S+\)|phaseB\(\S+\)) host_bytes=\d+ host_pages=(\d+) gc_pages=(\d+) WAF=([\d.]+)', line) or \
             re.match(r'(phaseA\(\S+\)|phaseB\(\S+\)) host_pages=(\d+) gc_pages=(\d+) WAF=([\d.]+)', line)
        if mm and int(mm[2]) > 0: add('mix:' + m[1], mm[1], m[2], mm[4], mm[2])
groups = collections.defaultdict(lambda: collections.defaultdict(list))
for g, w, p, waf, host in rows: groups[(g, w)][p].append(waf)
print(f'{"group":10s} {"workload":18s} ' + ' '.join(f'{p:>12s}' for p in POL))
for (g, w) in sorted(groups):
    cells = []
    for p in POL:
        v = groups[(g, w)].get(p)
        cells.append(f'{st.fmean(v):.3f}({len(v)})' if v else '-')
    print(f'{g:10s} {w:18s} ' + ' '.join(f'{c:>12s}' for c in cells))
if '-v' in sys.argv:
    for r in sorted(rows): print(r)
