#!/usr/bin/env bash
# 11-24 E1 rerun after the SQLITE_FULL fix (result/revision-20261123/mixR kept untouched as invalid evidence).
# Starts only if the validation run (revision-validate-20261124.sh) passed every condition; then mixR x3,
# rep 1..3 interleaved onlinev4 / onlinev4nodrift / onlinev4fullreset (same seeds per rep, MULT=3, same ops as before).
# Unlike the 11-23 queue, the first failed run stops the queue (a failure now means a real problem, not noise).
cd /home/oy/iCAT; V=$PWD/result/revision-20261124/validation; B=$PWD/result/revision-20261124/mixR; mkdir -p $B
until grep -q '^exit=' $V/verdict.txt 2>/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 60; done
v=$V/verdict.txt
pass() { grep -qx 'exit=0' $v && grep -qx 'ok' $v && grep -qx 'sqlite_full=0' $v \
  && grep -q 'ycsb-load.txt bad_lines=0 ops=300000 ok=300000 expected=300000' $v \
  && grep -q 'ycsb-run-B.txt bad_lines=0 ops=42000000 ok=42000000 expected=42000000' $v \
  && (( $(sed -n 's/^min_mnt_avail_mb=//p' $v) > 64 )); }
pass || { echo "VALIDATION FAILED - not starting reruns $(date -Is)"; cat $v; exit 1; }
echo "validation passed $(date -Is)"
run() { # run <policy> <rep>
  echo "start $1 rep$2 $(date -Is) disk=$(df --output=avail -h / | tail -1)"
  sha256sum buildoutput/nvmev-online-${1#online}.ko script/mix-20260911.sh > $B/$1-rep$2.module.sha256
  git rev-parse HEAD > $B/$1-rep$2.commit.txt
  env MIX_BASE=$B MULT=3 bash script/mix-20260911.sh mixR $1 $2 > $B/mixR-$1-rep$2.console.txt 2>&1
  local rc=$?; until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done
  git add $B EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "revision-20261124: mixR $1 rep$2 exit=$rc" >/dev/null 2>&1; git push -q 2>/dev/null
  ((rc == 0)) && echo "[done] $1 rep$2 $(date -Is)" || { echo "FAIL $1 rep$2 exit=$rc $(date -Is) - stopping queue"; exit 1; }
}
for r in 1 2 3; do for p in onlinev4 onlinev4nodrift onlinev4fullreset; do run $p $r; done; done
echo RERUNQUEUEDONE $(date -Is)
