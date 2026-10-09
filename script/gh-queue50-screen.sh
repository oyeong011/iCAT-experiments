#!/usr/bin/env bash
# queue50 (10-09 23:10): the pre-registered screening (webproxy, fileserver x CAT-47/CAT-37, 30 min each) on THIS PC — the device
# was idle and the second PC had not started it. Launched with "hold=script/sqlite.sh".
cd /home/oy/iCAT; R=result/screen-20261008; mkdir -p $R
pkill -f "gh-queue49-mixX.sh" 2>/dev/null
for w in scrWP scrFS; do for p in fixed47 fixed37; do
  until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
  echo "start $w $p $(date -Is)"; env PH_SECS=1800 bash script/screen-20261008.sh $w $p 1 > $R/$w-$p.console.txt 2>&1 || echo "FAIL $w $p"
done; done
git add $R script/gh-queue50-screen.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "screening webproxy/fileserver done" >/dev/null 2>&1; git push -q 2>/dev/null
echo QUEUE50DONE $(date -Is); sleep 86400
