#!/usr/bin/env bash
# queue49 (10-09 13:00): rerun mixX CAT-37 after fio segfaulted in the prep step at 04:58 (before measuring). Launched with "hold=script/sqlite.sh".
cd /home/oy/iCAT; R=result/cycle-20261007
pkill -f "gh-queue48-mixX.sh" 2>/dev/null
until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
echo "start 10h fixed37 $(date -Is)"
env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX fixed37 1 > $R/mixX-fixed37-rep1.console.txt 2>&1 || echo "FAIL fixed37"
git add $R script/gh-queue49-mixX.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "mixX: 10h fixed37 (rerun)" >/dev/null 2>&1; git push -q 2>/dev/null
echo QUEUE49DONE $(date -Is); sleep 86400
