#!/usr/bin/env bash
# 11-24 pre-check before rerunning E1: one full mixR x3 run (phase A, full YCSB phase B, phase C) with the fixed runner
# (300k records, mkfs -m 0, YCSB fail-fast + count check, space log, integrity check). Validation only: not counted in E1.
# Pass = exit 0, SQLITE_FULL 0, YCSB errors 0, ops == ok == expected, min free space > 0, integrity ok.
cd /home/oy/iCAT; B=$PWD/result/revision-20261124/validation; mkdir -p $B
git rev-parse HEAD > $B/commit.txt; sha256sum buildoutput/nvmev-online-v4.ko script/mix-20260911.sh > $B/module.sha256
echo "start validation $(date -Is) rootfs_free=$(df --output=avail -h / | tail -1)"
env MIX_BASE=$B MULT=3 bash script/mix-20260911.sh mixR onlinev4 1 > $B/console.txt 2>&1; rc=$?
d=$B/mixR-onlinev4-rep1-x3
{ echo "exit=$rc"; cat $d/ycsb-check.txt; cat $d/sqlite-integrity.txt
  echo "sqlite_full=$(zcat $d/ycsb-run-B.txt.gz | grep -c SQLITE_FULL)"
  echo "min_mnt_avail_mb=$(grep -o 'mnt_avail_mb=[0-9]*' $d/control-series.txt | cut -d= -f2 | sort -n | head -1)"
  cat $d/space.txt; } > $B/verdict.txt 2>&1
echo "VALIDATIONDONE exit=$rc $(date -Is)"
