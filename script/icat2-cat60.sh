#!/usr/bin/env bash
# For the SECOND PC (Codex), 10-13: finish the 60-arm baseline on the 90-min mix (FIO-Fast 30 min -> Varmail 30 min -> OLTP 30 min).
# This PC already has arm00 + arm30..59 and runs arm29..16. Second PC: arm03 -> arm15 ascending (arm00..02 done there 10-09).
# Pre-registered in EXPERIMENT_LOG.md ("고정 CAT 60조합 나머지 — 2026-10-13"). Usage: git pull; bash script/icat2-cat60.sh
# A failed check does not stop the sweep: the run is marked FAIL and the next arm starts. Results are pushed after each arm.
set -u
cd ~/iCAT
B=result/cat60-90min-pc2-20261013; mkdir -p $B
for a in $(seq 3 15); do
  p=arm$(printf %02d $a)
  [[ -f $B/mixY-$p-rep1/summary.txt ]] && continue
  [[ -f buildoutput/nvmev-$p.ko ]] || { echo "missing buildoutput/nvmev-$p.ko (build varmail-compare-src FIXED_ARM=$a)"; exit 1; }
  until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done
  echo "start $p $(date -Is)"
  env MIXY_SEQ="F V O" PH_SECS=1800 MIX_BASE=$PWD/$B bash script/mix-gc-20261010.sh mixY $p 1 > $B/$p.console.txt 2>&1 || echo "FAIL $p"
  echo "$p $(grep '^total' $B/mixY-$p-rep1/summary.txt 2>/dev/null | sed 's/.*WAF=//')" >> $B/totals.txt
  git add $B EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "cat60 PC2: $p" >/dev/null 2>&1; git pull -q --rebase 2>/dev/null; git push -q 2>/dev/null
done
echo "PC2 CAT60 DONE $(date -Is)"
