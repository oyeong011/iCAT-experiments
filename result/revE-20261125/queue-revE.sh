#!/usr/bin/env bash
# revE-20261125 queue (고컴): waits for the revC main queue to finish normally, then smoke 120 s for the 3 policies, check-run on
# each smoke, then queue-order.registered.txt (pre-registered order/seeds). After every run: check-run.py (anomaly -> stop, the next
# run is NOT started) and sync-push.sh (between measurements). Never touches nvme0n1 (safety-env.sh). Device lock shared with revC.
C=/home/oy/iCAT/result/revE-20261125; RC=/home/oy/iCAT/result/revC-20261124; J=/home/oy/iCAT/EXPERIMENT_LOG.md; L=$C/queue.log
echo $$ > $C/queue.pid
busy() { [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; }
while kill -0 "$(cat $RC/queue-main.pid)" 2>/dev/null; do sleep 30; done
grep -q "main queue finished" $RC/queue-main.log || { echo "$(date -Is) revC did not finish normally; revE NOT started" >> $L; exit 1; }
busy && { echo "$(date -Is) device occupied; revE NOT started" >> $L; exit 1; }
kill "$(cat $RC/loadsampler.pid)" 2>/dev/null   # revC sampler is no longer needed (revC finished)
setsid nohup $C/loadsampler.sh > /dev/null 2>&1 < /dev/null &
echo "$(date -Is) revE starts (revC finished)" >> $L
printf -- '\n### revE-20261125 queue started %s (after revC finished): smokes revE-v4, revE-noelim, revE-drift12, then 9 runs (queue-order.registered.txt)\n' "$(date -Is)" >> $J
for pol in revE-v4 revE-noelim revE-drift12; do
  echo "$(date -Is) start smoke $pol" >> $L
  $C/run-one.sh "$pol" 1 smoke; rc=$?
  echo "$(date -Is) end smoke $pol exit=$rc" >> $L
  printf -- '- revE-20261125 smoke %s finished %s exit=%s, evidence `%s`\n' "$pol" "$(date -Is)" "$rc" "$C/raw/mixFYF-$pol-rep1-smoke120" >> $J
  python3 -I $C/check-run.py $C/raw/mixFYF-$pol-rep1-smoke120 >> $L 2>&1; ck=$?
  if (( rc != 0 || ck != 0 )) || busy; then echo "$(date -Is) ANOMALY smoke $pol (exit=$rc check=$ck); main queue NOT started" >> $L; $C/sync-push.sh; exit 1; fi
done
echo "$(date -Is) all 3 smokes passed; main queue starts" >> $L; $C/sync-push.sh
while read -r pol rep; do
  [[ -e $C/raw/mixFYF-$pol-rep$rep ]] && { echo "$(date -Is) skip existing $pol rep$rep" >> $L; continue; }
  echo "$(date -Is) start $pol rep$rep" >> $L
  $C/run-one.sh "$pol" "$rep"; rc=$?
  echo "$(date -Is) end $pol rep$rep exit=$rc" >> $L
  printf -- '- revE-20261125 %s rep%s finished %s exit=%s, evidence `%s`\n' "$pol" "$rep" "$(date -Is)" "$rc" "$C/raw/mixFYF-$pol-rep$rep" >> $J
  python3 -I $C/check-run.py $C/raw/mixFYF-$pol-rep$rep >> $L 2>&1; ck=$?
  $C/sync-push.sh "mixFYF-$pol-rep$rep"
  if (( rc != 0 || ck != 0 )) || busy; then
    echo "$(date -Is) ANOMALY after $pol rep$rep (exit=$rc check=$ck); queue stopped, next run NOT started" >> $L
    printf -- '- revE-20261125 queue stopped after %s rep%s: exit=%s check=%s (see checks.tsv)\n' "$pol" "$rep" "$rc" "$ck" >> $J
    exit 1
  fi
done < $C/queue-order.registered.txt
echo "$(date -Is) main queue finished" >> $L; $C/sync-push.sh
