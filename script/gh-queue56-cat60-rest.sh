#!/usr/bin/env bash
# queue56 (10-13, user: fill the 60-arm baseline, split with the second PC; check whether v7's "2nd place" survives).
# After queue55: arm29 -> arm16 (descending) on the same 90-min mix (F V O), then repeats v7 x2 and arm47 x2 (rep2, rep3).
# Second PC runs arm03 -> arm15 with script/icat2-cat60.sh. Pre-registered in EXPERIMENT_LOG.md 2026-10-13.
cd /home/oy/iCAT; B=result/cat60-90min-thispc-20261011; R=result/v7-20261011
push() { git add $B $R script/gh-queue56*.sh script/icat2-cat60.sh >/dev/null 2>&1; git commit -qm "$1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
until grep -q QUEUE55DONE result/queue55.out 2>/dev/null; do sleep 60; done
idle() { until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; }
run() {  # run <policy> <rep> <base dir> <totals label>
  [[ -f $3/mixY-$1-rep$2/summary.txt ]] && return; idle; echo "start $1 rep$2 $(date -Is)"
  env MIXY_SEQ="F V O" PH_SECS=1800 MIX_BASE=$PWD/$3 bash script/mix-gc-20261010.sh mixY $1 $2 > $3/$1-rep$2.console.txt 2>&1 || echo "FAIL $1 rep$2"
  echo "$4 $(grep '^total' $3/mixY-$1-rep$2/summary.txt 2>/dev/null | sed 's/.*WAF=//')" >> $3/totals.txt; push "cat60 this PC: $4"
}
# 10-13 12:00: arm01-29 already done by the second PC (branch origin/icat-2, result/mixX-cat60-90min-20261009/) -> sweep removed, repeats only
mkdir -p $R/fvo90-rep
for r in 2 3; do run onlinev7 $r $R/fvo90-rep v7-rep$r; run arm47 $r $B arm47-rep$r; done
echo QUEUE56DONE $(date -Is)
