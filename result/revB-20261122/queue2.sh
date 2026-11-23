#!/usr/bin/env bash
# revB-20261122 queue v2 (11-22 19:50, user: finish as fast as possible): arm60 reps 2,3 dropped; same order otherwise.
# Waits for the bridge run (revB-v4 rep1, started by queue.sh) to exit, records it, then runs queue-order-v2.txt.
C=/home/oy/iCAT/result/revB-20261122; BR=${1:?bridge run-one pid}
echo $$ > $C/queue2.pid
while kill -0 "$BR" 2>/dev/null; do sleep 20; done
rc=$(awk -F'\t' '$2=="mixFYF-revB-v4-rep1"{print $3}' $C/runs.tsv | tail -1)
echo "$(date -Is) end revB-v4 rep1 exit=${rc:-unknown} (recorded by queue2)" >> $C/queue.log
printf -- '- revB-20261122 revB-v4 rep1 finished %s exit=%s, evidence `%s`\n' "$(date -Is)" "${rc:-unknown}" "$C/raw/mixFYF-revB-v4-rep1" >> /home/oy/iCAT/EXPERIMENT_LOG.md
if [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; then echo "$(date -Is) device still occupied; queue2 stopped" >> $C/queue.log; exit 1; fi
while read -r pol rep; do
  [[ -e $C/raw/mixFYF-$pol-rep$rep ]] && { echo "$(date -Is) skip existing $pol rep$rep" >> $C/queue.log; continue; }
  echo "$(date -Is) start $pol rep$rep" >> $C/queue.log
  $C/run-one.sh "$pol" "$rep"; rc=$?
  echo "$(date -Is) end $pol rep$rep exit=$rc" >> $C/queue.log
  printf -- '- revB-20261122 %s rep%s finished %s exit=%s, evidence `%s`\n' "$pol" "$rep" "$(date -Is)" "$rc" "$C/raw/mixFYF-$pol-rep$rep" >> /home/oy/iCAT/EXPERIMENT_LOG.md
  if [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; then echo "$(date -Is) device still occupied; queue stopped" >> $C/queue.log; exit 1; fi
done < $C/queue-order-v2.txt
echo "$(date -Is) queue finished" >> $C/queue.log
