#!/usr/bin/env bash
# revC-20261124 main queue (user 11-24: concurrency explicitly allowed). Waits for queue.sh (smokes) to exit, requires all
# 4 smokes exit 0 and check-run OK, then runs queue-order.registered.txt (pre-registered order and seeds unchanged).
# After every run: check-run.py (anomaly -> stop, do not continue) and sync-push.sh (between measurements).
C=/home/oy/iCAT/result/revC-20261124; J=/home/oy/iCAT/EXPERIMENT_LOG.md; L=$C/queue-main.log
echo $$ > $C/queue-main.pid
busy() { [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; }
while kill -0 "$(cat $C/queue.pid)" 2>/dev/null; do sleep 20; done
for pol in revC-v4 revC-elim10 revC-elim25 online; do
  d=$C/raw/mixFYF-$pol-rep1-smoke120
  python3 -I $C/check-run.py $d >> $L 2>&1 || { echo "$(date -Is) smoke check failed: $pol -> main queue NOT started" >> $L; $C/sync-push.sh; exit 1; }
done
busy && { echo "$(date -Is) device occupied; main queue not started" >> $L; exit 1; }
echo "$(date -Is) all 4 smokes passed; main queue starts" >> $L; $C/sync-push.sh
while read -r pol rep; do
  [[ -e $C/raw/mixFYF-$pol-rep$rep ]] && { echo "$(date -Is) skip existing $pol rep$rep" >> $L; continue; }
  echo "$(date -Is) start $pol rep$rep" >> $L
  $C/run-one.sh "$pol" "$rep"; rc=$?
  echo "$(date -Is) end $pol rep$rep exit=$rc" >> $L
  printf -- '- revC-20261124 %s rep%s finished %s exit=%s, evidence `%s`\n' "$pol" "$rep" "$(date -Is)" "$rc" "$C/raw/mixFYF-$pol-rep$rep" >> $J
  python3 -I $C/check-run.py $C/raw/mixFYF-$pol-rep$rep >> $L 2>&1; ck=$?
  $C/sync-push.sh "mixFYF-$pol-rep$rep"
  if (( rc != 0 || ck != 0 )) || busy; then
    echo "$(date -Is) ANOMALY after $pol rep$rep (exit=$rc check=$ck); queue stopped, next run NOT started" >> $L
    printf -- '- revC-20261124 queue stopped after %s rep%s: exit=%s check=%s (see checks.tsv)\n' "$pol" "$rep" "$rc" "$ck" >> $J
    exit 1
  fi
done < $C/queue-order.registered.txt
echo "$(date -Is) main queue finished" >> $L; $C/sync-push.sh
