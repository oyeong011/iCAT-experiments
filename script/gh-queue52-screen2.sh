#!/usr/bin/env bash
# queue52 (10-10): second screening round on THIS PC after mixY CAT-47 (queue51): FIO-Shift (test5, 2 x 900 s), webserver,
# YCSB-A uniform 300k — 30 min each, CAT-47 and CAT-37. Same rule: WAF < 1.2 -> cut. Launched with "hold=script/sqlite.sh".
cd /home/oy/iCAT; R=result/screen-20261008
until grep -q QUEUE51DONE result/queue51.out 2>/dev/null; do sleep 60; done
pkill -f "gh-queue51-mixY.sh" 2>/dev/null
for w in scrSH scrYU scrWS; do for p in fixed47 fixed37; do
  until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
  echo "start $w $p $(date -Is)"; env PH_SECS=1800 bash script/screen-20261008.sh $w $p 1 > $R/$w-$p.console.txt 2>&1 || echo "FAIL $w $p"
done; done
git add $R script/gh-queue52-screen2.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "screening round 2 done" >/dev/null 2>&1; git push -q 2>/dev/null
echo QUEUE52DONE $(date -Is); sleep 86400
