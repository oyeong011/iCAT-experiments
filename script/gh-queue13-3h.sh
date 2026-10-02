#!/usr/bin/env bash
# 3-hour fast 3-region runs (MULT=18): v2 gets 30 min forced sweep + 2.5 h to learn. Runs after queue11 (QUEUE7DONE), before the slow sweep (queue10).
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE7DONE $S/queue7.out 2>/dev/null; do sleep 300; done
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "3h runs: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
for x in "onlinev2 1" "fixed47 1" "onlinev2 2" "online 1" "fixed50 1"; do set -- $x
  d=t4-$1-rep$2-x18; [[ -e $R/$d/summary.txt ]] && continue; rm -rf $R/$d
  MULT=18 bash script/mix-20260911.sh t4 $1 $2 > $R/$d.console.txt 2>&1 || echo "FAIL $d"; push "$d"
done
echo QUEUE13DONE $(date -Is)
