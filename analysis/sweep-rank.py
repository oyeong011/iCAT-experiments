#!/usr/bin/env python3
"""Rank the 60 arms measured on this machine (sweep-20260915) and compare with the GitHub sweep.  python3 analysis/sweep-rank.py [test4|sqlite-a|oltp]"""
import re, glob, sys
from pathlib import Path
R = Path('/home/oy/iCAT/result'); wl = sys.argv[1] if len(sys.argv) > 1 else 'test4'
GC = re.compile(r'GC stats: .*?policy=(\S+) host_pages=(\d+) gc_pages=(\d+)')
def name(a):  # arm index -> kKK-sSSS-rRR
    k = [2, 4, 7, 10][a // 15]; s = [25, 50, 100, 200, 400][(a // 3) % 5]; r = [4, 7, 16][a % 3]
    return f'k{k:02d}-s{s:03d}-r{r:02d}'
ours = {}
for a in range(60):
    t = f'arm{a:02d}'
    if wl == 'test4':
        c = R / 'sweep-20260915' / f'test4-{t}.console.txt'
        if not c.exists(): continue
        m = re.search(r'^\[RESULT\] (\S+)', c.read_text(errors='replace'), re.M)
        if not m or not Path(m[1]).exists(): continue
        g = GC.findall(Path(m[1]).read_text(errors='replace'))
    else:
        c = R / ('sqlite' if wl == 'sqlite-a' else 'filebench') / (f'a-{t}.console.txt' if wl == 'sqlite-a' else f'oltp-{t}.console.txt')
        if not c.exists(): continue
        w = re.search(r'^\[WAF\] module=\S+ WAF=([\d.]+) host_pages=(\d+)', c.read_text(errors='replace'), re.M)
        g = [('x', w[2], str(round((float(w[1]) - 1) * int(w[2]))))] if w else []
    if g: ours[a] = (int(g[-1][1]) + int(g[-1][2])) / int(g[-1][1])
gh = {}
txt = (R / 'gh-sweep-analysis-20260911' / 'per-arm-waf.txt').read_text()
blk = re.search(rf'^{wl} .*?(?=^\S|\Z)', txt, re.M | re.S)
if blk:
    for n, w in re.findall(r'\n +(k\d\d-s\d\d\d-r\d\d) ([\d.]+)', blk[0]): gh[n] = float(w)
print(f'{wl}: 이 머신 {len(ours)}/60 완료.  rank  arm  (k,scale,ratio)   WAF     GitHub WAF  GitHub rank')
ghrank = {n: i + 1 for i, (n, _) in enumerate(sorted(gh.items(), key=lambda x: x[1]))}
for i, (a, w) in enumerate(sorted(ours.items(), key=lambda x: x[1])):
    n = name(a); tag = {10: ' ←최악', 37: ' ←기본', 47: ' ←최적', 50: ' ←견고'}.get(a, '')
    print(f'{i+1:4d}  arm{a:02d}  {n}  {w:.4f}   {gh.get(n, float("nan")):.4f}   {ghrank.get(n, "-"):>3}{tag}')
if len(ours) == 60 and gh:
    import statistics as st
    xs = [ours[a] for a in range(60)]; ys = [gh[name(a)] for a in range(60)]
    rx = {v: i for i, v in enumerate(sorted(xs))}; ry = {v: i for i, v in enumerate(sorted(ys))}
    d2 = sum((rx[x] - ry[y]) ** 2 for x, y in zip(xs, ys)); n = 60
    print(f'\nSpearman rho (이 머신 vs GitHub 순위) = {1 - 6 * d2 / (n * (n * n - 1)):.3f}')
    print(f'이 머신 최저 {min(xs):.4f} 최고 {max(xs):.4f} 편차 {(max(xs)/min(xs)-1)*100:.1f}%  |  GitHub 최저 {min(ys):.4f} 최고 {max(ys):.4f} 편차 {(max(ys)/min(ys)-1)*100:.1f}%')
