#!/usr/bin/env python3
"""batchG-20261126 drift50 runtime check. usage: drift-check.py <run dir>   (exit 1 = queue stops)
Gate: every `WATGC_V2 reset reason=waf-drift` line satisfies |sample - reference| * 65536 > reference * 32768 (50 %),
the exact kernel comparison with WATGC_V2_DRIFT_Q16 = 32768 (conv_ftl.c 569-577).
Info: reset count, min ratio, and windows in a settled best-arm state whose deviation is in (25 %, 50 %] (would count at V4's 25 %)."""
import re, sys
from pathlib import Path
d = Path(sys.argv[1]); kl = (d / 'kernel.log').read_text(errors='replace')
bad, ratios = 0, []
for m in re.finditer(r'WATGC_V2 reset .*part=(\d) .*window=(\d+) .*reference_q16=(\d+) sample_q16=(\d+)', kl):
    p, w, r, s = map(int, m.groups()); ok = abs(s - r) * 65536 > r * 32768; bad += not ok; ratios.append(abs(s - r) / r)
    print(f'reset part={p} window={w} ref={r} sample={s} dev={abs(s - r) / r:.3f} {"OK" if ok else "BELOW_50%"}')
ref, mid = {}, 0
for l in kl.splitlines():
    if (m := re.search(r'WATGC_V2 settled .*part=(\d) .*waf_q16=(\d+)', l)): ref[int(m[1])] = int(m[2])
    elif (m := re.search(r'WATGC_V2 reset .*part=(\d)', l)): ref.pop(int(m[1]), None)
    elif (m := re.search(r'WATGC_V2 sample .*part=(\d) .*evaluated=(\d+) .*waf_q16=(\d+) best=(\d+) .*settled=1', l)):
        p, ev, w, b = map(int, m.groups())
        if p in ref and ev == b and ref[p] * 16384 < abs(w - ref[p]) * 65536 <= ref[p] * 32768: mid += 1
print(f'resets={len(ratios)} min_dev={min(ratios) if ratios else None} below_threshold={bad} settled_best_windows_dev_25_50pct={mid}')
print('DRIFT_CHECK'); print('OK' if bad == 0 else 'FAIL'); sys.exit(1 if bad else 0)
