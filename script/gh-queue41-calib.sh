#!/usr/bin/env bash
# queue41 (10-06): calibration mixW1 then mixW2 (CAT-47). Launched with "hold=script/sqlite.sh" so older queues keep waiting.
cd /home/oy/iCAT; R=result/inherit-20261006
for l in mixW1 mixW2; do
  until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
  echo "start $l $(date -Is)"; env PH_SECS=900 bash script/mix-inherit-20261006.sh $l fixed47 1 > $R/$l-fixed47.console.txt 2>&1 || echo "FAIL $l"
done
git add $R/mixW* script/mix-inherit-20261006.sh script/gh-queue41-calib.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "calibration mixW1/W2 done" >/dev/null 2>&1; git push -q 2>/dev/null
echo QUEUE41DONE $(date -Is)
# keep holding the device for the decision that follows (killed by hand)
sleep 86400
