#!/usr/bin/env bash
# param-20261127 queue v2 (11-27, host split by parameter group: 승컴 = UCB C group only; gamma group -> 고컴).
# Waits for the in-flight pf-c075 smoke (started by queue.sh v1) to finish, checks it, then runs the C-group main order
# (queue-order.v2-Cgroup.txt = C lines of queue-order.registered.txt, same relative order). Same checks / stop-on-anomaly as v1.
C=/home/oy/iCAT/result/param-20261127; L=$C/queue.log; cd /home/oy/iCAT
busy() { [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; }
inflight() { pgrep -f '[r]un-one.sh pf-' >/dev/null || pgrep -f '[r]unner-param.sh' >/dev/null; }
ck() { python3 -I $C/check-run.py "$1" >> $L 2>&1 || return 1; python3 -I -B $C/param-check.py "$1" > "$1/param-check.txt" 2>&1 || { echo "$(date -Is) PARAM_CHECK FAIL $1" >> $L; return 1; }; }
push() { git add $C >/dev/null 2>&1; git commit -qm "param-20261127: $1" >/dev/null 2>&1; git push -q 2>/dev/null; }
echo "$(date -Is) queue-v2 (C group) waiting for in-flight smoke" >> $L
while inflight; do sleep 30; done; sleep 5
busy && { echo "$(date -Is) device occupied after smoke; v2 not started" >> $L; exit 1; }
s=$C/raw/mixFYF-pf-c075-rep1-smoke120
rc=$(cat $s/exit-code.txt 2>/dev/null)
ck $s && [[ "$rc" == 0 ]] || { echo "$(date -Is) smoke failed: pf-c075 (exit=$rc) - main NOT started" >> $L; push "smoke failed pf-c075"; exit 1; }
echo "$(date -Is) C-group smokes passed (pf-c050, pf-c075)" >> $L; push "C-group smokes"
while read -r pol rep; do
  d=$C/raw/mixFYF-$pol-rep$rep
  [[ -e $d ]] && { echo "$(date -Is) skip existing $pol rep$rep" >> $L; continue; }
  echo "$(date -Is) start $pol rep$rep" >> $L
  $C/run-one.sh "$pol" "$rep"; rc=$?
  ck $d; c=$?
  echo "$(date -Is) end $pol rep$rep exit=$rc check=$c" >> $L; push "mixFYF $pol rep$rep exit=$rc check=$c"
  (( rc == 0 && c == 0 )) && ! busy || { echo "$(date -Is) ANOMALY - queue stopped" >> $L; exit 1; }
done < $C/queue-order.v2-Cgroup.txt
echo "$(date -Is) PARAMQUEUEDONE" >> $L; push "queue done (C group)"
