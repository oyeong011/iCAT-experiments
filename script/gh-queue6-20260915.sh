#!/usr/bin/env bash
# Master mix queue: 14 designs x 6 policies x 3 seeds, core designs first; then single-workload leftovers. Push per block.
set -u
cd /home/oy/iCAT
push() { git add -A >/dev/null 2>&1; git commit -qm "results: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
POL="greedy fixed10 fixed37 fixed47 fixed50 online"
CORE="mixA mixB mixC mixD mixJ mixG"; MORE="mixK mixL mixM mixQ"; AUX="mixO mixP mixH mixF"
run_mix() { local lb=$1 m=$2 rep=$3
  [[ -e result/mix-20260911/$lb-$m-rep$rep/summary.txt ]] && return 0
  rm -rf result/mix-20260911/$lb-$m-rep$rep
  bash script/mix-20260911.sh $lb $m $rep > result/mix-20260911/$lb-$m-rep$rep.console.txt 2>&1 || echo "FAIL $lb $m rep$rep"; }
for rep in 1 2 3; do
  for grp in "$CORE" "$MORE" "$AUX"; do for lb in $grp; do
    for m in $POL; do run_mix $lb $m $rep; done
    push "$lb x 6 policies rep$rep"
  done; done
done
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
  [[ -e result/mix-20260911/main-$m/summary.txt ]] || bash script/mix-20260911.sh main $m 1 > result/mix-20260911/main-$m.console.txt 2>&1 || echo "FAIL main $m"
done; push "main design, remaining policies"
echo QUEUE6DONE $(date -Is)
