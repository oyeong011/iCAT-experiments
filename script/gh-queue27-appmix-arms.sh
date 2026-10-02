#!/usr/bin/env bash
# 2026-09-29: rank v4 on the four mixes where it beat robust CAT against the usual top fixed arms (same x3 length). Replaces queue26's v1 10 h.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
free() { until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done; }
free
push() { git add -A >/dev/null 2>&1; git commit -qm "appmix arms: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; fio --version >/dev/null 2>&1 || { echo "fio broken before $d"; return; }
  "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
run t4-onlinev3probe-rep1-x18 env MULT=18 bash script/mix-20260911.sh t4 onlinev3probe 1; push "ablation onlinev3probe 3 h"
for lb in mixO mixF mixJ mixP; do for p in fixed47 arm46 arm31 arm17 fixed37; do run $lb-$p-rep1-x3 env MULT=3 VM_RUN=900 bash script/mix-20260911.sh $lb $p 1; done; push "$lb 5 arms x3"; done
python3 analysis/all-tables.py > /dev/null 2>&1; push "RESULTS_ALL regenerated"
echo QUEUE27DONE $(date -Is)
