#!/usr/bin/env bash
# queue54 (10-11): iCAT-v7 (window = 1024 GC cycles only, burn-in 256 GC; otherwise v6) after the baseline (queue53).
# 1) same 90-min mix as the 60-arm baseline (F V O, 30 min each) -> directly comparable to the ranking
# 2) mixY 20 phases (same order as v6 / CAT-47 mixY) -> does v7 fix the FIO-Slow loss (v6 3.265 vs CAT-47 2.864)?
# Launched with "hold=script/sqlite.sh". The runner is edited only here, after queue53 has finished (never while it runs).
cd /home/oy/iCAT; R=result/v7-20261011; mkdir -p $R
until grep -q QUEUE53DONE result/queue53.out 2>/dev/null; do sleep 60; done
pkill -f "gh-queue53-cat60.sh" 2>/dev/null
grep -q 'onlinev7)' script/mix-gc-20261010.sh || sed -i '/^    onlinev6) module=/a\    onlinev7) module="$root/buildoutput/nvmev-online-v7.ko";;   # 10-11: v6 + window ends after 1024 GC cycles (no 512 MiB host condition), burn-in 256 GC' script/mix-gc-20261010.sh
bash -n script/mix-gc-20261010.sh || { echo "SYNTAX FAIL"; exit 1; }
push() { git add $R script/gh-queue54-v7.sh script/mix-gc-20261010.sh online-v7-src buildoutput/build-online-v7.log EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "v7: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
run() { until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
  mkdir -p $R/$1; echo "start $1 $(date -Is)"; env MIXY_SEQ="$2" PH_SECS=1800 MIX_BASE=$PWD/$R/$1 bash script/mix-gc-20261010.sh mixY onlinev7 1 > $R/$1.console.txt 2>&1 || echo "FAIL $1"
  echo "$1 $(grep '^total' $R/$1/mixY-onlinev7-rep1/summary.txt 2>/dev/null | sed 's/.*WAF=//')" >> $R/totals.txt; push "$1"; }
run fvo90 "F V O"
run mixY "$(cat result/gc-20261010/mixy-seq.txt)"
echo QUEUE54DONE $(date -Is); sleep 86400
