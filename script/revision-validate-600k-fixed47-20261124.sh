#!/usr/bin/env bash
# 11-24 plan A validation (one run only): mixR6 = mixR with 600k records, test.dat removed before phase B,
# 11-24 (user-approved, one run): same as revision-validate-600k-20261124.sh but fixed47, to separate device-state vs learner causes of the phase-C WAF jump (4.72).
# Writes verdict.txt with every pass condition; does NOT start any further runs.
cd /home/oy/iCAT; B=$PWD/result/revision-20261124/validation-600k-fixed47; mkdir -p $B
git rev-parse HEAD > $B/commit.txt; sha256sum buildoutput/nvmev-varmail-20260908-fixed47.ko script/mix-20260911.sh > $B/module.sha256
echo "start validation-600k-fixed47 $(date -Is) rootfs_free=$(df --output=avail -h / | tail -1)"
env MIX_BASE=$B MULT=3 bash script/mix-20260911.sh mixR6 fixed47 1 > $B/console.txt 2>&1; rc=$?
until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done
d=$B/mixR6-fixed47-rep1-x3
chk() { printf '%-28s %s\n' "$1" "$2"; }
{
  chk exit "$rc"
  chk module_unloaded "$([[ -e /sys/module/nvmev ]] && echo NO || echo yes)"
  chk umounted "$(mountpoint -q mnt && echo NO || echo yes)"
  cat $d/ycsb-check.txt
  chk sqlite_full "$(zcat $d/ycsb-run-B.txt.gz $d/ycsb-load.txt.gz 2>/dev/null | grep -c SQLITE_)"
  chk ycsb_abort "$([[ -f $d/ycsb-abort.txt ]] && cat $d/ycsb-abort.txt || echo none)"
  chk integrity "$(cat $d/sqlite-integrity.txt 2>/dev/null)"
  for s in A B R C; do chk "phase_$s" "$([[ -f $d/phase-$s-end.txt ]] && echo done || echo MISSING)"; done
  chk fio_errors "$(jq -s '[.[].jobs[] | select(.error != 0)] | length' $d/phase-A.json $d/phase-R-preset.json $d/phase-C.json 2>&1)"
  chk kernel_errors "$(grep -cE 'BUG:|WARNING:|Oops|Call Trace|nvmev.*(error|fail)' $d/kernel.log)"
  chk ycsb_log_bytes "$(stat -c %s $d/ycsb-run-B.txt.gz 2>/dev/null)"
  chk min_mnt_avail_mb "$(grep -o 'mnt_avail_mb=[0-9]*' $d/control-series.txt | cut -d= -f2 | sort -n | head -1)"
  cat $d/space.txt; cat $d/testdat-stat-A.txt $d/testdat-stat-R.txt
  cat $d/summary.txt
} > $B/verdict.txt 2>&1
echo "VALIDATION600KF47DONE exit=$rc $(date -Is)"
# arm per partition at every phase boundary (fixed47 must stay 47) and per-phase raw counters incl. NAND = host + gc
{ for f in $d/started.txt $d/phase-*-start.txt $d/phase-*-end.txt $d/final-control.txt; do printf '%s arms=%s gc_count=%s\n' "${f##*/}" "$(grep -o 'arm=[0-9]*' $f | cut -d= -f2 | tr '\n' ,)" "$(grep -o 'gc_count=[0-9]*' $f | cut -d= -f2 | tr '\n' ,)"; done; } > $B/arms-and-gccount.txt
