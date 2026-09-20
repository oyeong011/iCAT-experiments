#!/usr/bin/env bash
# iCAT v2 (reward window x6) — starts automatically after queue6 (QUEUE6DONE). Same workloads as v1; only the online policy is re-run.
set -u
cd /home/oy/iCAT
Q=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad/queue6.out
until grep -q QUEUE6DONE "$Q" 2>/dev/null; do sleep 120; done
push() { git add -A >/dev/null 2>&1; git commit -qm "v2 results: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
M=online-v2
# 0. smoke + the reference single workload with explicit measurement (3 seeds)
SMOKE=1 bash script/mix-20260911.sh t4 onlinev2 1 > result/mix-20260911/t4-onlinev2-smoke.console.txt 2>&1 || echo "FAIL smoke v2"
for r in 1 2 3; do bash script/mix-20260911.sh t4 onlinev2 $r > result/mix-20260911/t4-onlinev2-rep$r.console.txt 2>&1 || echo "FAIL t4 v2 rep$r"; done
push "t4 x3"
# 0a. redo the phase-length v2 runs (first v2 build discarded every window: MAX_WINDOW_GC cap)
for mult in 3 6; do for lb in mixA mixC; do MULT=$mult bash script/mix-20260911.sh $lb onlinev2 1 > result/mix-20260911/$lb-onlinev2-rep1-x$mult.console.txt 2>&1 || echo "FAIL $lb v2 x$mult"; done; done
push "phase-length v2 redo"
# 0b. 3600 s test4: enough for v2 (60 s windows) to sweep all 60 arms and settle; v1 long reference = long-online (1.952)
for r in 1 2; do bash script/mix-20260911.sh t4long onlinev2 $r > result/mix-20260911/t4long-onlinev2-rep$r.console.txt 2>&1 || echo "FAIL t4long v2 rep$r"; done
bash script/mix-20260911.sh t4long fixed47 1 > result/mix-20260911/t4long-fixed47-rep1.console.txt 2>&1 || echo "FAIL t4long fixed47"
push "t4long v2 x2 + fixed47"
# 1. single workloads, GitHub method (same scripts as v1)
for s in "" -s2 -s3; do for t in test4 test3 test5 test2; do
  [[ "$t" == test2 && -n "$s" ]] && continue
  GH_TEST_JOB=gh-$t$s.fio bash script/gh-fio.sh $M > result/gh-repro-20260914/$t${s}-$M.console.txt 2>&1 || echo "FAIL $t$s v2"
done; done; push "fio x 3 seeds"
for rep in 1 2 3; do for w in a b; do bash script/sqlite.sh $M $w > result/sqlite/$w-$M-rep$rep.console.txt 2>&1 || echo "FAIL sqlite $w v2 rep$rep"; cp result/sqlite/workload$w/dmesg-$M.log result/sqlite/workload$w/dmesg-$M-rep$rep.log 2>/dev/null; done; done; push "sqlite x3"
for rep in 1 2 3; do for w in oltp varmail; do FILEBENCH_RUNTIME=300 bash script/gh-filebench.sh $M $w > result/filebench/$w-$M-rep$rep.console.txt 2>&1 || echo "FAIL $w v2 rep$rep"; cp result/filebench/$w/dmesg-$M.log result/filebench/$w/dmesg-$M-rep$rep.log 2>/dev/null; done; done; push "filebench x3"
# 2. mixes, 3 seeds, core first
for rep in 1 2 3; do for lb in mixA mixB mixC mixD mixJ mixG mixK mixL mixM mixQ mixO mixP mixH mixF; do
  [[ -e result/mix-20260911/$lb-onlinev2-rep$rep/summary.txt ]] && continue
  rm -rf result/mix-20260911/$lb-onlinev2-rep$rep
  bash script/mix-20260911.sh $lb onlinev2 $rep > result/mix-20260911/$lb-onlinev2-rep$rep.console.txt 2>&1 || echo "FAIL $lb v2 rep$rep"
done; push "mixes rep$rep"; done
echo QUEUE7DONE $(date -Is)
