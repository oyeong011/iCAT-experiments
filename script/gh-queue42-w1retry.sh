#!/usr/bin/env bash
# queue42 (10-06): mixW1 retry after a JVM segfault in the YCSB load (12:36); runs after mixW2. Holds the device afterwards.
cd /home/oy/iCAT; R=result/inherit-20261006
until [[ -f $R/mixW2-fixed47/exit-code.txt ]] && [[ ! -e /sys/module/nvmev ]]; do sleep 5; done
pkill -f "gh-queue41-calib.sh" 2>/dev/null   # it only sleeps (holding) after mixW2; this queue holds instead
mv $R/mixW1-fixed47 $R/mixW1-fixed47-failed-jvmsegv; mv $R/mixW1-fixed47.console.txt $R/mixW1-fixed47-failed-jvmsegv.console.txt
echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
echo "start mixW1 retry $(date -Is)"; env PH_SECS=900 bash script/mix-inherit-20261006.sh mixW1 fixed47 1 > $R/mixW1-fixed47.console.txt 2>&1 || echo "FAIL mixW1 retry"
git add $R/mixW* script/gh-queue42-w1retry.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "calibration mixW1 retry, mixW2" >/dev/null 2>&1; git push -q 2>/dev/null
echo QUEUE42DONE $(date -Is); sleep 86400
