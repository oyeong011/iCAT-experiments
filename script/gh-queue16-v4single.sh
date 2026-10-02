#!/usr/bin/env bash
# v4 on fast 3-region writes, same lengths as v3 (60 min x2, 3 h x1). After queue12.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE12DONE $S/queue12.out 2>/dev/null; do sleep 300; done
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "v4 single: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d; "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
for r in 1 2; do run t4long-onlinev4-rep$r bash script/mix-20260911.sh t4long onlinev4 $r; done; push "t4long 60 min x2"
run t4-onlinev4-rep1-x18 env MULT=18 bash script/mix-20260911.sh t4 onlinev4 1; push "t4 3 h"
echo QUEUE16DONE $(date -Is)
