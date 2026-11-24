#!/usr/bin/env bash
# revC-20261124 queue (고컴): smoke 120 s for the 4 modules new to this runner, then queue-order.txt.
# Stops on the first failed run or if the device is still occupied. Never touches nvme0n1 (safety-env.sh).
C=/home/oy/iCAT/result/revC-20261124; J=/home/oy/iCAT/EXPERIMENT_LOG.md
echo $$ > $C/queue.pid
busy() { [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; }
busy && { echo "$(date -Is) device occupied at start; queue not started" >> $C/queue.log; exit 1; }
for pol in revC-v4 revC-elim10 revC-elim25 online; do
  echo "$(date -Is) start smoke $pol" >> $C/queue.log
  $C/run-one.sh "$pol" 1 smoke; rc=$?
  echo "$(date -Is) end smoke $pol exit=$rc" >> $C/queue.log
  printf -- '- revC-20261124 smoke %s finished %s exit=%s, evidence `%s`\n' "$pol" "$(date -Is)" "$rc" "$C/raw/mixFYF-$pol-rep1-smoke120" >> $J
  if (( rc != 0 )) || busy; then echo "$(date -Is) smoke failed or device occupied; queue stopped" >> $C/queue.log; exit 1; fi
done
while read -r pol rep; do
  [[ -e $C/raw/mixFYF-$pol-rep$rep ]] && { echo "$(date -Is) skip existing $pol rep$rep" >> $C/queue.log; continue; }
  echo "$(date -Is) start $pol rep$rep" >> $C/queue.log
  $C/run-one.sh "$pol" "$rep"; rc=$?
  echo "$(date -Is) end $pol rep$rep exit=$rc" >> $C/queue.log
  printf -- '- revC-20261124 %s rep%s finished %s exit=%s, evidence `%s`\n' "$pol" "$rep" "$(date -Is)" "$rc" "$C/raw/mixFYF-$pol-rep$rep" >> $J
  if (( rc != 0 )) || busy; then echo "$(date -Is) run failed or device occupied; queue stopped" >> $C/queue.log; exit 1; fi
done < $C/queue-order.txt
echo "$(date -Is) queue finished" >> $C/queue.log
