#!/usr/bin/env bash
# 60-arm sweep on two mixes (A: test4->sqlite-a, C: test3->test4), seed 1. Runs after PHASELENDONE, then resumes queue6 (v1 mix) and queue7 (v2).
set -u
cd /home/oy/iCAT
B=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q PHASELENDONE $B/queue8.out 2>/dev/null; do sleep 60; done
until ! pgrep -f "script/(gh-fio|gh-filebench|sqlite|mix-20260911)\.sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "mixsweep: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
for lb in mixA mixC; do for a in $(seq 0 59); do t=$(printf 'arm%02d' $a)
  [[ -e result/mix-20260911/$lb-$t-rep1/summary.txt ]] && continue
  rm -rf result/mix-20260911/$lb-$t-rep1
  bash script/mix-20260911.sh $lb $t 1 > result/mix-20260911/$lb-$t-rep1.console.txt 2>&1 || echo "FAIL $lb $t"
  (( a % 20 == 19 )) && push "$lb arms to $t"
done; push "$lb x 60 arms"; done
echo MIXSWEEPDONE $(date -Is)
(setsid nohup bash script/gh-queue6-20260915.sh > $B/queue6.out 2>&1 < /dev/null &)
(setsid nohup bash script/gh-queue7-v2.sh > $B/queue7.out 2>&1 < /dev/null &)
