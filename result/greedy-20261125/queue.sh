#!/usr/bin/env bash
# greedy-20261125 Online Greedy queue (M3). NOT STARTED until the user approves. Smokes (120 s, 3 policies) must pass check-run,
# then the pre-registered order runs; any anomaly stops the queue (no automatic continuation). Results are pushed after each run.
C=/home/oy/iCAT/result/greedy-20261125; L=$C/queue.log; cd /home/oy/iCAT
busy() { [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; }
ck() { python3 -I $C/check-run.py "$1" >> $L 2>&1 || return 1; [[ "$1" != *greedy-online* ]] || python3 -I -B $C/greedy-check.py "$1" > "$1/greedy-check.txt" 2>&1 || { echo "$(date -Is) GREEDY_CHECK FAIL $1" >> $L; return 1; }; }
push() { git add $C EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "greedy-20261125: $1" >/dev/null 2>&1; git push -q 2>/dev/null; }
busy && { echo "$(date -Is) device occupied; not started" >> $L; exit 1; }
for pol in $(cut -d" " -f1 $C/queue-order.registered.txt | sort -u); do
  $C/run-one.sh $pol 1 smoke; rc=$?
  ck $C/raw/mixFYF-$pol-rep1-smoke120 && (( rc == 0 )) || { echo "$(date -Is) smoke failed: $pol (exit=$rc) - main NOT started" >> $L; push "smoke failed $pol"; exit 1; }
done
echo "$(date -Is) smokes passed" >> $L; push smokes
while read -r pol rep; do
  [[ -e $C/raw/mixFYF-$pol-rep$rep ]] && { echo "$(date -Is) skip existing $pol rep$rep" >> $L; continue; }
  echo "$(date -Is) start $pol rep$rep" >> $L
  $C/run-one.sh "$pol" "$rep"; rc=$?
  ck $C/raw/mixFYF-$pol-rep$rep; c=$?
  echo "$(date -Is) end $pol rep$rep exit=$rc check=$c" >> $L; push "mixFYF $pol rep$rep exit=$rc check=$c"
  (( rc == 0 && c == 0 )) && ! busy || { echo "$(date -Is) ANOMALY - queue stopped" >> $L; exit 1; }
done < $C/queue-order.registered.txt
echo "$(date -Is) GREEDYQUEUEDONE" >> $L; push "queue done"
