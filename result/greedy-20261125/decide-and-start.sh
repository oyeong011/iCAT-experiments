#!/usr/bin/env bash
# greedy-20261125: wait for the ablation queue to end and the device to be free, apply the pre-registered V4 reuse rule
# (Welch 95% CI of abl-v4 - revD-v4 total WAF entirely inside [-0.02, +0.02]), record it, then start the greedy-only queue (3 runs).
C=/home/oy/iCAT/result/greedy-20261125; A=/home/oy/iCAT/result/revision-additional-ablation/queue.log; cd /home/oy/iCAT
until grep -qE 'ABLQUEUEDONE|ANOMALY|failed|not started' $A; do sleep 60; done
grep -q ABLQUEUEDONE $A || { echo "$(date -Is) ablation did not finish normally; greedy NOT started" > $C/control-decision.txt; exit 1; }
until [[ ! -e /sys/module/nvmev ]] && ! mountpoint -q mnt && flock -n result/mix-20260911/device.lock true; do sleep 30; done
python3 -I -B - > $C/control-decision.txt 2>&1 <<'P'
import sys, re, statistics as st
from pathlib import Path
from scipy import stats
sys.path.insert(0, '/home/oy/iCAT/analysis/revision'); import r_suite_20261125 as R
def w(g):
    out = []
    for d in sorted(Path('/home/oy/iCAT/result').glob(g)):
        ok, why = R.validity(d); (h, gc), _ = R.counters(d / 'stopped.txt')
        print(d.name, 'valid' if ok else 'INVALID ' + why, f'{1 + gc / h:.6f}'); out += [1 + gc / h] if ok else []
    return out
a, b = w('revD-20261124/raw/mixFYF-revD-v4-rep[123]'), w('revision-additional-ablation/raw/mixFYF-abl-v4-rep[123]')
assert len(a) == 3 and len(b) == 3, 'need 3 valid runs each'
va, vb = st.variance(a) / 3, st.variance(b) / 3; df = (va + vb) ** 2 / (va ** 2 / 2 + vb ** 2 / 2); h = stats.t.ppf(.975, df) * (va + vb) ** .5
d = st.mean(b) - st.mean(a); lo, hi = d - h, d + h
ok = -0.02 <= lo and hi <= 0.02
print(f'abl-v4 - revD-v4 total WAF diff={d:.5f} 95% CI [{lo:.5f}, {hi:.5f}] df={df:.2f} -> {"REUSE abl-v4" if ok else "FAIL: report and ask before adding V4 runs"}')
sys.exit(0 if ok else 3)
P
rc=$?; echo "$(date -Is) rule exit=$rc" >> $C/control-decision.txt
git add $C/control-decision.txt; git commit -qm "greedy-20261125: V4 reuse decision (rule exit=$rc)" ; git push -q
# 11-25 brief: greedy 3 runs start regardless of the rule; the rule only decides whether extra V4 runs are PROPOSED (never auto-run).
echo revD-v4 > $C/control.txt; cp $C/queue-order.greedy-only.txt $C/queue-order.registered.txt
git add $C; git commit -qm "greedy-20261125: control revD-v4 (reuse rule exit=$rc), greedy-only order registered; queue starting"; git push -q
exec bash $C/queue.sh
