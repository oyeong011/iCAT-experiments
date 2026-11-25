#!/usr/bin/env bash
# m1-20261126 queue (GoCom): waits for the revE queue to finish NORMALLY (never interrupts it), then
#  (0) userspace CPU benchmark (bench-sim.sh, device-free, machine otherwise idle)
#  (1) smoke mixY "F V S" x 120 s, SMOKE=1 payload, both modules (not used in results)
#  (2) 6 main mixY runs (20 phases x 1800 s, SEQ as SeungCom smartgc-20261119) in queue-order.registered.txt.
# After every run: check-m1.py, sync-push.sh. Stops if the device is not clean or the kernel logged an error;
# a workload-level failure (e.g. FIO timeout) is recorded as FAIL and the queue continues (pre-registered).
C=/home/oy/iCAT/result/m1-20261126; E=/home/oy/iCAT/result/revE-20261125; J=/home/oy/iCAT/EXPERIMENT_LOG.md; L=$C/queue.log
SEQ="F S V F V S F S V F V S F S V F V S F S"
echo $$ > $C/queue.pid; mkdir -p $C/raw $C/sampler $C/console
busy() { [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; }
while kill -0 "$(cat $E/queue.pid)" 2>/dev/null; do sleep 60; done
grep -q "main queue finished" $E/queue.log || { echo "$(date -Is) revE did not finish normally; m1 NOT started" >> $L; exit 1; }
for i in $(seq 30); do busy || break; sleep 10; done
busy && { echo "$(date -Is) device occupied; m1 NOT started" >> $L; exit 1; }
sleep 120   # let revE sync-push finish
echo "$(date -Is) m1 starts (revE finished)" >> $L
printf -- '\n### m1-20261126 queue started %s (after revE finished): sim CPU benchmark, smokes m1-icat-v4 / m1-smartgc-eq8, 6 mixY runs (queue-order.registered.txt). Pre-registration result/m1-20261126/preregistration.md\n' "$(date -Is)" >> $J
echo "$(date -Is) start sim benchmark" >> $L
$C/bench-sim.sh > $C/console/bench-sim.txt 2>&1; echo "$(date -Is) end sim benchmark: $(tail -1 $C/console/bench-sim.txt)" >> $L
$C/sync-push.sh
run() { # run <policy> <rep> [smoke]
  local pol=$1 rep=$2 smoke=${3:-} args name rc ck
  [[ $pol == m1-icat-v4 ]] && args="icat_seed=$((2026111400 + rep))" || args="smartgc_seed=$rep"
  name=mixY-$pol-rep$rep${smoke:+-smoke}
  $C/sampler.sh $C/sampler/$name & local sp=$!
  sleep 65
  echo "$(date -Is) start $name" >> $L
  if [[ -n $smoke ]]; then
    env SMOKE=1 MIXY_SEQ="F V S" PH_SECS=120 M1_REP_DIR=1 MIX_BASE=$C/raw M1_SHA=$C/modules.sha256 MOD_ARGS="$args" \
      bash $C/runner-m1.sh mixY $pol $rep > $C/console/$name.txt 2>&1; rc=$?
  else
    env MIXY_SEQ="$SEQ" PH_SECS=1800 M1_REP_DIR=1 MIX_BASE=$C/raw M1_SHA=$C/modules.sha256 MOD_ARGS="$args" \
      bash $C/runner-m1.sh mixY $pol $rep > $C/console/$name.txt 2>&1; rc=$?
  fi
  wait $sp
  echo "$(date -Is) end $name exit=$rc" >> $L
  python3 -I $C/check-m1.py $C/raw/$name $C/sampler/$name >> $C/checks.tsv 2>> $L; ck=$?
  tail -1 $C/checks.tsv >> $L
  printf -- '- m1-20261126 %s finished %s exit=%s check=%s, evidence `%s`\n' "$name" "$(date -Is)" "$rc" "$ck" "$C/raw/$name" >> $J
  $C/sync-push.sh "$name"
  if busy || grep -qE 'kernel-errors|module-sha' <(tail -1 $C/checks.tsv); then
    echo "$(date -Is) ANOMALY after $name (exit=$rc check=$ck, device busy or kernel error); queue stopped" >> $L; exit 1; fi
  if [[ -n $smoke ]] && (( rc != 0 || ck != 0 )); then echo "$(date -Is) ANOMALY smoke $name (exit=$rc check=$ck); main NOT started" >> $L; exit 1; fi
  (( rc == 0 && ck == 0 )) || echo "$(date -Is) RUN FAILED $name (exit=$rc check=$ck): recorded as failed, not excluded; queue continues" >> $L
}
for pol in m1-icat-v4 m1-smartgc-eq8; do run $pol 1 smoke; done
echo "$(date -Is) both smokes passed; main queue starts" >> $L
while read -r pol rep; do
  [[ -e $C/raw/mixY-$pol-rep$rep ]] && { echo "$(date -Is) skip existing $pol rep$rep" >> $L; continue; }
  run "$pol" "$rep"
done < $C/queue-order.registered.txt
echo "$(date -Is) main queue finished" >> $L; $C/sync-push.sh
