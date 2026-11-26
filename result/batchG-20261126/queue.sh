#!/usr/bin/env bash
# batchG-20261126 queue (M6 drift50, M3 Greedy GC, same-batch V4). Smokes (120 s, 3 policies) must pass check-run, then the
# pre-registered order runs; any anomaly stops the queue (no automatic continuation). Raw logs are pushed after each run.
C=/home/oy/iCAT/result/batchG-20261126; L=$C/queue.log; cd /home/oy/iCAT
raw() { case $1 in drift50) echo result/drift50-20261126/raw;; greedygc) echo result/greedygc-20261126/raw;; *) echo $C/raw;; esac; }
busy() { [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; }
ck() { python3 -I $C/check-run.py "$1" >> $L 2>&1 || return 1; [[ "$1" != *drift50* ]] || python3 -I -B $C/drift-check.py "$1" > "$1/drift-check.txt" 2>&1 || { echo "$(date -Is) DRIFT_CHECK FAIL $1" >> $L; return 1; }; }
push() { git add $C result/drift50-20261126 result/greedygc-20261126 >/dev/null 2>&1; git commit -qm "batchG-20261126: $1" >/dev/null 2>&1; git push -q 2>/dev/null; }
busy && { echo "$(date -Is) device occupied; not started" >> $L; exit 1; }
for pol in $(cut -d" " -f1 $C/queue-order.registered.txt | sort -u); do
  $C/run-one.sh $pol 1 smoke; rc=$?
  ck $(raw $pol)/mixFYF-$pol-rep1-smoke120 && (( rc == 0 )) || { echo "$(date -Is) smoke failed: $pol (exit=$rc) - main NOT started" >> $L; push "smoke failed $pol"; exit 1; }
done
echo "$(date -Is) smokes passed" >> $L; push smokes
while read -r pol rep; do
  d=$(raw $pol)/mixFYF-$pol-rep$rep
  [[ -e $d ]] && { echo "$(date -Is) skip existing $pol rep$rep" >> $L; continue; }
  echo "$(date -Is) start $pol rep$rep" >> $L
  $C/run-one.sh "$pol" "$rep"; rc=$?
  ck $d; c=$?
  echo "$(date -Is) end $pol rep$rep exit=$rc check=$c" >> $L; push "mixFYF $pol rep$rep exit=$rc check=$c"
  (( rc == 0 && c == 0 )) && ! busy || { echo "$(date -Is) ANOMALY - queue stopped" >> $L; exit 1; }
done < $C/queue-order.registered.txt
echo "$(date -Is) BATCHGQUEUEDONE" >> $L; push "queue done"
