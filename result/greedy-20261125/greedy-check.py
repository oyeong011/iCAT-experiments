#!/usr/bin/env python3
"""greedy-20261125 independent rule check for one run dir (greedy-online only): exit 1 on any mismatch.
Replays the kernel log: first windows must be distinct arms; after all 45 arms are seen, every logged `next` must equal
argmin over arms of floor-Q16(1 + sum gc / sum host) of all windows so far (undiscounted), ties -> lowest arm index."""
import re, sys
from collections import Counter
from pathlib import Path
d = Path(sys.argv[1]); ARMS = range(15, 60)
s = [tuple(map(int, m.groups())) for m in re.finditer(r'WATGC_V2 sample .*part=(\d) epoch=\d+ window=(\d+) .*evaluated=(\d+) .*host=(\d+) gc_pages=(\d+) .*next=(\d+)', (d / 'kernel.log').read_text(errors='replace'))]
bad = []
for part in range(4):
    w = [x for x in s if x[0] == part]; H, G, seen, checked = Counter(), Counter(), set(), 0
    first = [x[2] for x in w[:45]]
    if len(set(first)) != len(first): bad.append(f'part {part}: repeated arm in first {len(first)} windows')
    for _, win, a, h, g, nxt in w:
        H[a] += h; G[a] += g; seen.add(a)
        if len(seen) < 45:
            if nxt in seen and nxt != a: bad.append(f'part {part} win {win}: revisits {nxt} before coverage')
            continue
        exp = min(ARMS, key=lambda i: (65536 + G[i] * 65536 // H[i], i)); checked += 1
        if nxt != exp: bad.append(f'part {part} win {win}: next={nxt} expected={exp}')
    print(f'part {part}: windows={len(w)} distinct_first={len(set(first))} greedy_checked={checked}')
print('GREEDY_CHECK', 'OK' if not bad else 'FAIL', *bad[:10], sep='\n')
sys.exit(1 if bad else 0)
