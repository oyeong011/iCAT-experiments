#!/usr/bin/env bash
# revB-20261122 main queue: runs queue-order.txt in order; skips runs whose raw dir already exists (no overwrite).
C=/home/oy/iCAT/result/revB-20261122
echo $$ > $C/queue.pid
while read -r pol rep; do
  [[ -e $C/raw/mixFYF-$pol-rep$rep ]] && { echo "$(date -Is) skip existing $pol rep$rep" >> $C/queue.log; continue; }
  echo "$(date -Is) start $pol rep$rep" >> $C/queue.log
  $C/run-one.sh "$pol" "$rep"; rc=$?
  echo "$(date -Is) end $pol rep$rep exit=$rc" >> $C/queue.log
  printf -- '- revB-20261122 %s rep%s finished %s exit=%s, evidence `%s`\n' "$pol" "$rep" "$(date -Is)" "$rc" "$C/raw/mixFYF-$pol-rep$rep" >> /home/oy/iCAT/EXPERIMENT_LOG.md
  # stop the queue if the device was left occupied (module/mount cleanup failure)
  if [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; then echo "$(date -Is) device still occupied; queue stopped" >> $C/queue.log; exit 1; fi
done < $C/queue-order.txt
echo "$(date -Is) queue finished" >> $C/queue.log
