#!/usr/bin/env bash
# 아주 느린 3영역 쓰기(test4 IOPS/16, 1200 s) 60-arm sweep + greedy. GitHub measurement method (gh-fio.sh).
# Question: does the best scale move from 25% (fast) to >=200% (slow)?  Starts after queue14 (v3).
set -u
cd /home/oy/iCAT
B=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE14DONE $B/queue14.out 2>/dev/null; do sleep 300; done
until ! pgrep -f "script/mix-20260911.sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "sweep-slow16: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
D=result/sweep-slow16-20260921; mkdir -p $D
for t in greedy $(seq -f 'arm%02g' 0 59); do
  m=$t; [[ $t != greedy ]] || m=gh-greedy
  [[ -e $D/slow16-$t.console.txt ]] || GH_TEST_JOB=gh-test4-slow16.fio bash script/gh-fio.sh $m > $D/slow16-$t.console.txt 2>&1 || echo "FAIL slow16 $t"
  [[ $t != arm14 && $t != arm29 && $t != arm44 ]] || push "slow16 through $t"
done; push "slow16 x 60 arms + greedy"
python3 analysis/sweep-rank.py slow16 > $D/rank-slow16.txt 2>&1; push "slow16 rank"
echo QUEUE10DONE $(date -Is)
