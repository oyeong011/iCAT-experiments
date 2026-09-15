#!/usr/bin/env bash
# Full 60-arm sweep on this machine (GitHub measurement method): test4, sqlite-a, oltp. Then resume queue6 (v1 mixes) and queue7 (v2).
set -u
cd /home/oy/iCAT
B=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q BUILDDONE $B/build60.out 2>/dev/null; do sleep 30; done
until ! pgrep -f "script/mix-20260911.sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "sweep: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
mkdir -p result/sweep-20260915
for a in $(seq 0 59); do t=$(printf 'arm%02d' $a)
  [[ -e result/sweep-20260915/test4-$t.console.txt ]] || GH_TEST_JOB=gh-test4.fio bash script/gh-fio.sh $t > result/sweep-20260915/test4-$t.console.txt 2>&1 || echo "FAIL test4 $t"
done; push "test4 x 60 arms"
for a in $(seq 0 59); do t=$(printf 'arm%02d' $a)
  [[ -e result/sqlite/a-$t.console.txt ]] || bash script/sqlite.sh $t a > result/sqlite/a-$t.console.txt 2>&1 || echo "FAIL sqlite-a $t"
done; push "sqlite-a x 60 arms"
for a in $(seq 0 59); do t=$(printf 'arm%02d' $a)
  [[ -e result/filebench/oltp-$t.console.txt ]] || FILEBENCH_RUNTIME=300 bash script/gh-filebench.sh $t oltp > result/filebench/oltp-$t.console.txt 2>&1 || echo "FAIL oltp $t"
done; push "oltp x 60 arms"
echo SWEEPDONE $(date -Is)
# resume v1 mixes then v2
(setsid nohup bash script/gh-queue6-20260915.sh > $B/queue6.out 2>&1 < /dev/null &)
(setsid nohup bash script/gh-queue7-v2.sh > $B/queue7.out 2>&1 < /dev/null &)
