#!/usr/bin/env bash
# 2026-09-28: after queue24 — ① mail-server key 15 arms ② v3 ablations (3 h each) ③ v1 10 h. Drop from the end if time runs out.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE24DONE $S/queue24.out 2>/dev/null; do sleep 120; done
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "extras: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d; "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
# 1. mail server (filebench varmail, 150k files, 300 s), key 15 arms + greedy
D=result/sweep-varmail-20260928; mkdir -p $D
for t in gh-greedy arm17 arm20 arm23 arm26 arm29 arm31 arm34 arm37 arm40 arm43 arm47 arm50 arm53 arm56 arm59; do
  [[ -e $D/varmail-$t.console.txt ]] || FILEBENCH_RUNTIME=300 bash script/gh-filebench.sh $t varmail > $D/varmail-$t.console.txt 2>&1 || echo "FAIL varmail $t"
done
grep -H '^\[WAF\]' $D/varmail-*.console.txt | sed 's/ host_pages.*//' | sort -t= -k3 -n > $D/rank-varmail.txt; push "varmail key 15 arms"
# 2. v3 ablations, fast 3-region 3 h (compare v3 3 h 1.848)
for p in onlinev3k2 onlinev3probe; do run t4-$p-rep1-x18 env MULT=18 bash script/mix-20260911.sh t4 $p 1; push "ablation $p 3 h"; done
# 3. v1 10 h (compare v4 10 h 1.807)
run t4-online-rep1-x60 env MULT=60 bash script/mix-20260911.sh t4 online 1; push "v1 10 h"
python3 analysis/all-tables.py > /dev/null 2>&1; push "RESULTS_ALL regenerated"
echo QUEUE25DONE $(date -Is)
