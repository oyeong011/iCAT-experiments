#!/usr/bin/env bash
# queue53 (10-11): fixed-CAT baseline on THIS PC, same 90-min mix as the second PC's campaign (FIO-Fast 30 min -> Varmail 30 min
# -> OLTP 30 min, Table-3 prep). First arm00 again (cross-host check against the second PC's arm00 = 3.269), then arm59 down to arm30
# while the second PC goes up from arm03. Launched with "hold=script/sqlite.sh".
cd /home/oy/iCAT; R=result/cat60-90min-thispc-20261011; mkdir -p $R
until grep -q QUEUE52DONE result/queue52.out 2>/dev/null; do sleep 60; done
pkill -f "gh-queue52-screen2.sh" 2>/dev/null
push() { git add $R script/gh-queue53-cat60.sh script/mix-gc-20261010.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "cat60 this PC: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
for a in 00 $(seq 59 -1 30); do
  [[ -f $R/mixY-arm$a-rep1/summary.txt ]] && continue
  until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
  echo "start arm$a $(date -Is)"
  env MIXY_SEQ="F V O" PH_SECS=1800 MIX_BASE=$PWD/$R bash script/mix-gc-20261010.sh mixY arm$a 1 > $R/arm$a.console.txt 2>&1 || echo "FAIL arm$a"
  echo "arm$a $(grep '^total' $R/mixY-arm$a-rep1/summary.txt 2>/dev/null | sed 's/.*WAF=//')" >> $R/totals.txt
  push "arm$a"
done
echo QUEUE53DONE $(date -Is); sleep 86400
