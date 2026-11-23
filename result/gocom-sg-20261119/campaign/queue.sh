#!/bin/bash
# sg-20261119: mixY x4 in user-specified order; stop the queue if the device is not clean after a run.
cd /home/oy/iCAT; D=result/sg-20261119; SEQ="F S V F V S F S V F V S F S V F V S F S"
for p in smartgc smartgcq sg-greedy sg-arm47; do
  if [[ -e /sys/module/nvmev ]] || mountpoint -q mnt; then echo "$(date -Is) device not clean before $p; queue stopped" >> $D/queue.log; exit 1; fi
  echo "$(date -Is) start mixY $p" >> $D/queue.log
  env MIXY_SEQ="$SEQ" PH_SECS=1800 bash $D/mix-gc-20261010.local.sh mixY $p 1 > $D/mixY-$p.console.txt 2>&1; rc=$?
  echo "$(date -Is) end mixY $p exit=$rc" >> $D/queue.log
done
echo "$(date -Is) queue finished" >> $D/queue.log
