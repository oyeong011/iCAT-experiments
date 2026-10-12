#!/usr/bin/env bash
# queue55 (10-12, user: "run v7 here too"): replaces queue53/queue54 from arm34 on.
# Order: finish arm34 (already running, started by queue53) -> v7 90-min mix (F V O) -> baseline arm33..30 -> v7 mixY 20 phases.
# Launched with "hold=script/sqlite.sh". The runner gets the onlinev7 line only while no runner is running.
cd /home/oy/iCAT; B=result/cat60-90min-thispc-20261011; R=result/v7-20261011; mkdir -p $R
push() { git add $B $R script/gh-queue5[345]*.sh script/mix-gc-20261010.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "$1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
while pgrep -f "mix-gc-20261010.sh mixY arm34" >/dev/null; do sleep 30; done
echo "arm34 $(grep '^total' $B/mixY-arm34-rep1/summary.txt 2>/dev/null | sed 's/.*WAF=//')" >> $B/totals.txt; push "cat60 this PC: arm34"
grep -q 'onlinev7)' script/mix-gc-20261010.sh || sed -i '/^    onlinev6) module=/a\    onlinev7) module="$root/buildoutput/nvmev-online-v7.ko";;   # 10-11: v6 + window ends after 1024 GC cycles (no 512 MiB host condition), burn-in 256 GC' script/mix-gc-20261010.sh
bash -n script/mix-gc-20261010.sh || { echo "SYNTAX FAIL"; exit 1; }
idle() { until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; }
v7() { idle; mkdir -p $R/$1; echo "start v7 $1 $(date -Is)"; env MIXY_SEQ="$2" PH_SECS=1800 MIX_BASE=$PWD/$R/$1 bash script/mix-gc-20261010.sh mixY onlinev7 1 > $R/$1.console.txt 2>&1 || echo "FAIL $1"
  echo "$1 $(grep '^total' $R/$1/mixY-onlinev7-rep1/summary.txt 2>/dev/null | sed 's/.*WAF=//')" >> $R/totals.txt; push "v7: $1"; }
v7 fvo90 "F V O"
for a in 33 32 31 30; do
  [[ -f $B/mixY-arm$a-rep1/summary.txt ]] && continue
  idle; echo "start arm$a $(date -Is)"
  env MIXY_SEQ="F V O" PH_SECS=1800 MIX_BASE=$PWD/$B bash script/mix-gc-20261010.sh mixY arm$a 1 > $B/arm$a.console.txt 2>&1 || echo "FAIL arm$a"
  echo "arm$a $(grep '^total' $B/mixY-arm$a-rep1/summary.txt 2>/dev/null | sed 's/.*WAF=//')" >> $B/totals.txt; push "cat60 this PC: arm$a"
done
echo "BASELINE DONE $(date -Is)"
v7 mixY "$(cat result/gc-20261010/mixy-seq.txt)"
echo QUEUE55DONE $(date -Is); sleep 86400
