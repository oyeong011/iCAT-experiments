#!/usr/bin/env bash
# 2026-09-29: re-run the three queue25 runs that failed at 03:14 (fio symbol error from a corrupted page-cache copy of libceph-common; fixed by drop_caches).
# Guard: drop the page cache and check fio before every run.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "rerun: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; fio --version >/dev/null 2>&1 || { echo "fio broken before $d"; return; }
  "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
for p in onlinev3k2 onlinev3probe; do run t4-$p-rep1-x18 env MULT=18 bash script/mix-20260911.sh t4 $p 1; push "ablation $p 3 h"; done
run t4-online-rep1-x60 env MULT=60 bash script/mix-20260911.sh t4 online 1; push "v1 10 h"
python3 analysis/all-tables.py > /dev/null 2>&1; push "RESULTS_ALL regenerated"
echo QUEUE26DONE $(date -Is)
