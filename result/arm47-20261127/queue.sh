#!/usr/bin/env bash
# arm47-20261127 queue (fixed Arm 47 robustness, mixFYF n=3, 승컴). Structure = batchG-20261126 queue.sh (no drift check).
# Smoke (120 s) must pass check-run; then rep1..3; any anomaly stops the queue. Raw logs are pushed after each run.
C=/home/oy/iCAT/result/arm47-20261127; L=$C/queue.log; cd /home/oy/iCAT
busy() { [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; }
ck() { python3 -I $C/check-run.py "$1" >> $L 2>&1; }
push() { git add $C >/dev/null 2>&1; git commit -qm "arm47-20261127: $1" >/dev/null 2>&1; git push -q 2>/dev/null; }
busy && { echo "$(date -Is) device occupied; not started" >> $L; exit 1; }
$C/run-one.sh arm47 1 smoke; rc=$?
ck $C/raw/mixFYF-arm47-rep1-smoke120 && (( rc == 0 )) || { echo "$(date -Is) smoke failed (exit=$rc) - main NOT started" >> $L; push "smoke failed"; exit 1; }
echo "$(date -Is) smoke passed" >> $L; push smoke
for rep in 1 2 3; do
  d=$C/raw/mixFYF-arm47-rep$rep
  [[ -e $d ]] && { echo "$(date -Is) skip existing rep$rep" >> $L; continue; }
  echo "$(date -Is) start arm47 rep$rep" >> $L
  $C/run-one.sh arm47 "$rep"; rc=$?
  ck $d; c=$?
  echo "$(date -Is) end arm47 rep$rep exit=$rc check=$c" >> $L; push "mixFYF arm47 rep$rep exit=$rc check=$c"
  (( rc == 0 && c == 0 )) && ! busy || { echo "$(date -Is) ANOMALY - queue stopped" >> $L; exit 1; }
done
echo "$(date -Is) ARM47QUEUEDONE" >> $L; push "queue done"
