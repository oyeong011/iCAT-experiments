#!/usr/bin/env bash
# Mix-first queue (replaces queue3/queue4 remainder). Waits for the device to be free, then:
#   1. smoke mixB/mixC  2. rep1: mixA/mixB/mixC x 6 policies  3. rep2, rep3 same
#   4. leftovers: fio s3 (test3 fixed50/online, test5 x 6), filebench web x 4 policies + webproxy/videoserver cat37/online, main x 4 policies
set -u
cd /home/oy/iCAT
busy() { pgrep -f "script/(gh-fio|gh-filebench|gh-rocksdb|sqlite|mix-20260911)\.sh" >/dev/null || [[ -e /sys/module/nvmev ]]; }
until ! busy; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "results: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
POL="greedy fixed10 fixed37 fixed47 fixed50 online"
for lb in mixB mixC; do SMOKE=1 bash script/mix-20260911.sh $lb online 1 > result/mix-20260911/$lb-online-smoke.console.txt 2>&1 || echo "FAIL smoke $lb"; done
push "mixB/mixC smoke"
for rep in 1 2 3; do for lb in mixA mixB mixC; do
  for m in $POL; do
    [[ -e result/mix-20260911/$lb-$m-rep$rep/summary.txt ]] && continue
    rm -rf result/mix-20260911/$lb-$m-rep$rep
    bash script/mix-20260911.sh $lb $m $rep > result/mix-20260911/$lb-$m-rep$rep.console.txt 2>&1 || echo "FAIL $lb $m rep$rep"
  done
  push "$lb x 6 policies rep$rep"
done; done
for t in test3 test5; do for m in gh-greedy fixed10 gh-cat37 fixed47 fixed50 gh-online; do
  [[ -e result/gh-repro-20260914/$t-s3-$m.console.txt ]] && continue
  GH_TEST_JOB=gh-$t-s3.fio bash script/gh-fio.sh $m > result/gh-repro-20260914/$t-s3-$m.console.txt 2>&1 || echo "FAIL $t s3 $m"
done; done; push "fio seed s3 leftovers"
for w in webserver webproxy videoserver; do
  for m in gh-greedy fixed10 gh-cat37 fixed47 fixed50 gh-online; do
    [[ -e result/filebench/$w-$m.console.txt ]] && grep -q "^\[WAF\] module=.* WAF=[0-9]" result/filebench/$w-$m.console.txt && continue
    FILEBENCH_RUNTIME=300 bash script/gh-filebench.sh $m $w > result/filebench/$w-$m.console.txt 2>&1 || echo "FAIL $w $m"
    cp result/filebench/$w/dmesg-$m.log result/filebench/$w/dmesg-$m-rep1.log 2>/dev/null
  done; push "filebench $w x 6 policies"
done
for m in greedy fixed10 fixed37 fixed50; do
  bash script/mix-20260911.sh main $m 1 > result/mix-20260911/main-$m.console.txt 2>&1 || echo "FAIL main $m"
done; push "main design, remaining policies"
echo QUEUE5DONE $(date -Is)
