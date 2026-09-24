#!/usr/bin/env bash
# iCAT v3 on fast 3-region writes at 10 min / 30 min (x3) / 60 min / 3 h, plus two x6 mixes. After queue13, before queue10.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE13DONE $S/queue13.out 2>/dev/null; do sleep 300; done
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "v3: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d; "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
run t4-onlinev3-rep1 bash script/mix-20260911.sh t4 onlinev3 1; push "t4 10 min"
for r in 1 2 3; do run t4-onlinev3-rep$r-x3 env MULT=3 bash script/mix-20260911.sh t4 onlinev3 $r; done
for p in fixed47 onlinev2 online; do run t4-$p-rep1-x3 env MULT=3 bash script/mix-20260911.sh t4 $p 1; done; push "t4 30 min (x3)"
for r in 1 2; do run t4long-onlinev3-rep$r bash script/mix-20260911.sh t4long onlinev3 $r; done; push "t4long 60 min"
run t4-onlinev3-rep1-x18 env MULT=18 bash script/mix-20260911.sh t4 onlinev3 1; push "t4 3 h"
for lb in mixD mixK; do run $lb-onlinev3-rep1-x6 env MULT=6 bash script/mix-20260911.sh $lb onlinev3 1; done; push "mixD/mixK x6"
echo QUEUE14DONE $(date -Is)
