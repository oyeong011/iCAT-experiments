#!/usr/bin/env bash
# Phase length vs learning time: mixA (test4->sqlite-a) and mixC (test3->test4) with phases x1 (10 min, from queue6), x3 (30 min), x6 (60 min).
# Policies: online (v1), onlinev2, fixed47, fixed50. Runs after SWEEPDONE, before queue6 resumes (queue6/7 are launched by this script at the end).
set -u
cd /home/oy/iCAT
B=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q SWEEPDONE $B/sweep.out 2>/dev/null; do sleep 60; done
until ! pgrep -f "script/(gh-fio|gh-filebench|sqlite|mix-20260911)\.sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "phaselen: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
for mult in 3 6; do for lb in mixA mixC; do for m in online onlinev2 fixed47 fixed50; do
  [[ -e result/mix-20260911/$lb-$m-rep1-x$mult/summary.txt ]] && continue
  rm -rf result/mix-20260911/$lb-$m-rep1-x$mult
  MULT=$mult bash script/mix-20260911.sh $lb $m 1 > result/mix-20260911/$lb-$m-rep1-x$mult.console.txt 2>&1 || echo "FAIL $lb $m x$mult"
done; push "$lb x$mult"; done; done
echo PHASELENDONE $(date -Is)
(setsid nohup bash script/gh-queue6-20260915.sh > $B/queue6.out 2>&1 < /dev/null &)
(setsid nohup bash script/gh-queue7-v2.sh > $B/queue7.out 2>&1 < /dev/null &)
