#!/usr/bin/env bash
# Does this machine reproduce the original one? Fast 3-region writes, 10 min each, original-author method.
# Pass = every WAF within 1% of the original machine (arm47 1.746, arm50 1.786, gh-greedy 2.186 = mean of 3).
set -u
cd /home/oy/iCAT; o=result/validate-$(hostname)-$(date +%Y%m%d); mkdir -p "$o"
for t in arm47 arm50 gh-greedy; do GH_TEST_JOB=gh-test4.fio bash script/gh-fio.sh $t > "$o/$t.console.txt" 2>&1; done
python3 - "$o" <<'PY'
import re, sys, pathlib
ref = {'arm47': 1.7455, 'arm50': 1.7859, 'gh-greedy': 2.186}; ok = True
for t, r in ref.items():
    c = (pathlib.Path(sys.argv[1]) / f'{t}.console.txt').read_text(errors='replace')
    m = re.search(r'^\[RESULT\] (\S+)', c, re.M); g = re.findall(r'GC stats: .*?host_pages=(\d+) gc_pages=(\d+)', pathlib.Path(m[1]).read_text()) if m else []
    w = 1 + int(g[-1][1]) / int(g[-1][0]) if g else None
    d = (w / r - 1) * 100 if w else None; ok &= d is not None and abs(d) <= 1
    print(f'{t:10s} original {r:.3f}  here {w if w is None else round(w, 3)}  diff {d if d is None else f"{d:+.1f}%"}')
print('PASS' if ok else 'FAIL: do not mix this machine\'s results with the original machine\'s')
PY
