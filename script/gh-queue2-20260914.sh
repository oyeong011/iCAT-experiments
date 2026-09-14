#!/usr/bin/env bash
# Second unattended queue: waits for gh-queue-20260914 QUEUEDONE, then runs the 5-policy comparison
# (greedy / fixed10 worst / fixed47 oracle / fixed50 robust / cat37 & online already done) over every workload,
# then sqlite d, filebench videoserver, sqlite repeats. Pushes after each block. Failures are logged and skipped.
set -u
cd /home/oy/iCAT
Q=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad/queue.out
until grep -q QUEUEDONE "$Q" 2>/dev/null; do sleep 60; done
push() { git add -A >/dev/null 2>&1; git commit -qm "results: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
MODS="gh-greedy fixed10 fixed47 fixed50"
for t in test4 test3 test5 test2; do for m in $MODS; do
  GH_TEST_JOB=gh-$t.fio bash script/gh-fio.sh $m > result/gh-repro-20260914/$t-$m.console.txt 2>&1 || echo "FAIL $t $m"
done; push "fio $t x 4 policies"; done
for w in a b; do for m in $MODS; do
  bash script/sqlite.sh $m $w > result/sqlite/$w-$m.console.txt 2>&1 || echo "FAIL sqlite $w $m"
  cp result/sqlite/workload$w/dmesg-$m.log result/sqlite/workload$w/dmesg-$m-rep1.log 2>/dev/null
done; push "sqlite $w x 4 policies"; done
for w in oltp varmail; do for m in $MODS; do
  FILEBENCH_RUNTIME=300 bash script/gh-filebench.sh $m $w > result/filebench/$w-$m.console.txt 2>&1 || echo "FAIL $w $m"
  cp result/filebench/$w/dmesg-$m.log result/filebench/$w/dmesg-$m-rep1.log 2>/dev/null
done; push "filebench $w x 4 policies"; done
for m in gh-cat37 gh-online $MODS; do bash script/sqlite.sh $m d > result/sqlite/d-$m.console.txt 2>&1 || echo "FAIL sqlite d $m"; done; push "sqlite d"
for m in gh-cat37 gh-online; do FILEBENCH_RUNTIME=300 bash script/gh-filebench.sh $m videoserver > result/filebench/videoserver-$m.console.txt 2>&1 || echo "FAIL videoserver $m"; done; push "filebench videoserver"
for rep in 2 3; do for w in a b; do for m in gh-cat37 gh-online; do
  bash script/sqlite.sh $m $w > result/sqlite/$w-$m-rep$rep.console.txt 2>&1 || echo "FAIL sqlite $w $m rep$rep"
  cp result/sqlite/workload$w/dmesg-$m.log result/sqlite/workload$w/dmesg-$m-rep$rep.log 2>/dev/null
done; done; push "sqlite repeats rep$rep"; done
echo QUEUE2DONE $(date -Is)
