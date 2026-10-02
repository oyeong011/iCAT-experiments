#!/usr/bin/env bash
# iCAT v2 evaluated only on long runs (>=60 min). 10-min runs end inside v2's 30-min forced sweep (arms 0-19 = k2/k4 only), so they cannot evaluate learning.
# Takes over from queue7 after its long block ("t4long v2 x2 + fixed47"), drops queue7's short runs, then signals QUEUE7DONE for queue10.
set -u
cd /home/oy/iCAT
B=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q 't4long v2 x2 + fixed47' $B/queue7.out 2>/dev/null; do sleep 60; done
pkill -f 'bash script/gh-queue7-v2.sh' ; echo "queue7 stopped after long block $(date -Is)"
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "v2 long: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d; "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
# 1. 60-min fast 3-region: v2 3rd seed + every comparison policy at the same length
run t4long-onlinev2-rep3 bash script/mix-20260911.sh t4long onlinev2 3
for p in online fixed50 greedy; do run t4long-$p-rep1 bash script/mix-20260911.sh t4long $p 1; done
push "t4long 60 min: v2 rep3 + v1/fixed50/greedy"
# 2. x6 speed-change mixes (fast->slow, hot region shrinks), 4 policies
for lb in mixD mixK; do for p in onlinev2 online fixed47 fixed50; do run $lb-$p-rep1-x6 env MULT=6 bash script/mix-20260911.sh $lb $p 1; done; push "$lb x6 4 policies"; done
# 3. x6 seeds 2,3 for the two mixes that already have x6 rep1
for rep in 2 3; do for lb in mixC mixA; do run $lb-onlinev2-rep$rep-x6 env MULT=6 bash script/mix-20260911.sh $lb onlinev2 $rep; done; done
push "mixA/mixC x6 v2 seeds 2-3"
echo QUEUE7DONE $(date -Is) >> $B/queue7.out
echo QUEUE11DONE $(date -Is)
