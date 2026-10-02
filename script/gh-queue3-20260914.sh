#!/usr/bin/env bash
# Third unattended queue after QUEUE2DONE: fio seed variants x 6 policies, filebench web* x 4 policies, mix plan A x 4 policies.
set -u
cd /home/oy/iCAT
Q=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad/queue2.out
until grep -q QUEUE2DONE "$Q" 2>/dev/null; do sleep 60; done
push() { git add -A >/dev/null 2>&1; git commit -qm "results: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
ALL="gh-greedy fixed10 gh-cat37 fixed47 fixed50 gh-online"
for s in s2 s3; do for t in test4 test3 test5; do for m in $ALL; do
  GH_TEST_JOB=gh-$t-$s.fio bash script/gh-fio.sh $m > result/gh-repro-20260914/$t-$s-$m.console.txt 2>&1 || echo "FAIL $t $s $m"
done; done; push "fio seed $s x 6 policies"; done
for w in webserver webproxy videoserver; do for m in gh-greedy fixed10 fixed47 fixed50; do
  FILEBENCH_RUNTIME=300 bash script/gh-filebench.sh $m $w > result/filebench/$w-$m.console.txt 2>&1 || echo "FAIL $w $m"
  cp result/filebench/$w/dmesg-$m.log result/filebench/$w/dmesg-$m-rep1.log 2>/dev/null
done; push "filebench $w x 4 policies"; done
for rep in 1 2 3; do for m in fixed10 fixed47 fixed50 online; do
  bash script/mix-20260911.sh mixA $m $rep > result/mix-20260911/mixA-$m-rep$rep.console.txt 2>&1 || echo "FAIL mixA $m rep$rep"
done; push "mixA rep$rep"; done
echo QUEUE3DONE $(date -Is)
