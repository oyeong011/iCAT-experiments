#!/usr/bin/env bash
# Fourth unattended queue after QUEUE3DONE: every mix design x every policy (start/stop measurement).
#   mixA: test4 -> sqlite-a (fio file kept)      mixB: sqlite-a -> test4      mixC: test3 -> test4 (IOPS x4)
#   main: test4 -> rm -> sqlite-a (original, zombie data)   for the policies not yet run
set -u
cd /home/oy/iCAT
Q=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad/queue3.out
until grep -q QUEUE3DONE "$Q" 2>/dev/null; do sleep 60; done
push() { git add -A >/dev/null 2>&1; git commit -qm "results: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
# smoke the new modes first (1/10 size); a failure here is logged, the full runs still attempt
for lb in mixB mixC; do SMOKE=1 bash script/mix-20260911.sh $lb online 1 > result/mix-20260911/$lb-online-smoke.console.txt 2>&1 || echo "FAIL smoke $lb"; done
push "mixB/mixC smoke"
POL="greedy fixed10 fixed37 fixed47 fixed50 online"
for rep in 1 2 3; do
  for lb in mixB mixC; do for m in $POL; do
    bash script/mix-20260911.sh $lb $m $rep > result/mix-20260911/$lb-$m-rep$rep.console.txt 2>&1 || echo "FAIL $lb $m rep$rep"
  done; done
  for m in greedy fixed37; do   # mixA: fixed10/47/50/online already in queue3
    bash script/mix-20260911.sh mixA $m $rep > result/mix-20260911/mixA-$m-rep$rep.console.txt 2>&1 || echo "FAIL mixA $m rep$rep"
  done
  push "mixB/mixC x 6 + mixA greedy/fixed37, rep$rep"
done
for m in greedy fixed10 fixed37 fixed50; do   # original main design (delete file) for the policies not yet run; dir main-<policy>
  bash script/mix-20260911.sh main $m 1 > result/mix-20260911/main-$m.console.txt 2>&1 || echo "FAIL main $m"
done
push "main design, remaining policies"
echo QUEUE4DONE $(date -Is)
