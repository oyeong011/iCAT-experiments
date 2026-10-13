#!/usr/bin/env bash
# queue57 (10-13, user: mixY has only CAT-47; add default CAT-37 and robust CAT-50 so Fig 6(나) has the same baselines as 6(가)).
# After queue56: mixY (20 x 30 min, order in result/gc-20261010/mixy-seq.txt) with arm37 then arm50, rep1. Pre-registered in EXPERIMENT_LOG.md 2026-10-13.
cd /home/oy/iCAT; B=result/gc-20261010
until grep -q QUEUE56DONE result/queue56.out 2>/dev/null; do sleep 60; done
for p in arm37 arm50; do
  [[ -f $B/mixY-$p-rep1/summary.txt ]] && continue
  until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
  echo "start $p $(date -Is)"
  env MIXY_SEQ="$(cat $B/mixy-seq.txt)" PH_SECS=1800 MIX_BASE=$PWD/$B bash script/mix-gc-20261010.sh mixY $p 1 > $B/mixY-$p-rep1.console.txt 2>&1 || echo "FAIL $p"
  git add $B EXPERIMENT_LOG.md script/gh-queue57*.sh >/dev/null 2>&1; git commit -qm "mixY $p rep1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $p $(date -Is)"
done
echo QUEUE57DONE $(date -Is)
