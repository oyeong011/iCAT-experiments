#!/usr/bin/env bash
# param-20261127 queue (gamma 0.99/0.95/0.90, UCB C 0.50/0.75; n=3 each; 승컴). Copy of batchG queue.sh (paths, policies, param-check instead of drift-check).
# Smokes (120 s, 5 policies) must pass check-run + param-check, then the pre-registered order runs; any anomaly stops the queue. Raw logs pushed after each run.
C=/home/oy/iCAT/result/param-20261127; L=$C/queue.log; cd /home/oy/iCAT
raw() { echo $C/raw; }
busy() { [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; }
ck() { python3 -I $C/check-run.py "$1" >> $L 2>&1 || return 1; python3 -I -B $C/param-check.py "$1" > "$1/param-check.txt" 2>&1 || { echo "$(date -Is) PARAM_CHECK FAIL $1" >> $L; return 1; }; }
push() { git add $C >/dev/null 2>&1; git commit -qm "param-20261127: $1" >/dev/null 2>&1; git push -q 2>/dev/null; }
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
echo "$(date -Is) PARAMQUEUEDONE" >> $L; push "queue done"
