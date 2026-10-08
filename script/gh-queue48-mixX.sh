#!/usr/bin/env bash
# queue48 (10-08 18:55): mixX (frozen reference) CAT-50 then CAT-37 on THIS PC, so all four policies share one machine.
# Same runner/settings as the v6 and CAT-47 runs (short check already passed with this runner). Launched with "hold=script/sqlite.sh".
cd /home/oy/iCAT; R=result/cycle-20261007
pkill -f "gh-queue47-mixX.sh" 2>/dev/null
push() { git add $R script/gh-queue48-mixX.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "mixX: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
for p in fixed50 fixed37; do
  until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
  echo "start 10h $p $(date -Is)"
  env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX $p 1 > $R/mixX-$p-rep1.console.txt 2>&1 || echo "FAIL $p"
  push "10h $p"
done
echo QUEUE48DONE $(date -Is); sleep 86400
