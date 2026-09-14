#!/usr/bin/env bash
# Runs after the current batch (rest.out ALLDONE): repeats + remaining filebench workloads, git push after each block.
set -u
cd /home/oy/iCAT
until grep -q ALLDONE /tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad/rest.out 2>/dev/null; do sleep 60; done
push() { git add -A >/dev/null 2>&1; git commit -qm "results: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
push "batch 1 (test3/test5/test2/sqlite a,b)"
for rep in 2 3; do
  for t in test4 test3 test5; do for m in gh-cat37 gh-online; do
    GH_TEST_JOB=gh-$t.fio bash script/gh-fio.sh $m > result/gh-repro-20260914/$t-$m-rep$rep.console.txt 2>&1 || echo "FAIL $t $m rep$rep"
  done; done
  push "fio repeats rep$rep"
done
for rep in 2 3; do
  for w in oltp varmail; do for m in gh-cat37 gh-online; do
    FILEBENCH_RUNTIME=300 bash script/gh-filebench.sh $m $w > result/filebench/$w-$m-rep$rep.console.txt 2>&1 || echo "FAIL $w $m rep$rep"
    cp result/filebench/$w/dmesg-$m.log result/filebench/$w/dmesg-$m-rep$rep.log; cp result/filebench/$w/$m.txt result/filebench/$w/$m-rep$rep.txt   # original script overwrites fixed names
  done; done
  push "filebench repeats rep$rep"
done
for w in webserver webproxy; do for m in gh-cat37 gh-online; do
  FILEBENCH_RUNTIME=300 bash script/gh-filebench.sh $m $w > result/filebench/$w-$m.console.txt 2>&1 || echo "FAIL $w $m"
done; done
push "filebench webserver/webproxy"
echo QUEUEDONE $(date -Is)
