#!/usr/bin/env bash
# 2026-09-29: the fast 3-region 60-arm ranking mixed methods (arms: original-author method, learners: explicit window).
# Re-measure the top 12 arms + greedy with the explicit method (10 min each) so v1..v4 can be ranked with one ruler. After queue27.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE27DONE $S/queue27.out 2>/dev/null; do sleep 120; done
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "t4 explicit: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; fio --version >/dev/null 2>&1 || { echo "fio broken before $d"; return; }
  "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
for p in arm31 arm46 arm32 arm34 arm16 arm45 arm49 arm30 arm35 arm17 arm15 arm33 greedy fixed37; do run t4-$p-rep1 bash script/mix-20260911.sh t4 $p 1; done
push "top arms + greedy + default, explicit method"
python3 analysis/all-tables.py > /dev/null 2>&1; push "RESULTS_ALL regenerated"
echo QUEUE28DONE $(date -Is)
