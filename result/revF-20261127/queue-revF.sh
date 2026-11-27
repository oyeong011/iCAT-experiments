#!/usr/bin/env bash
# revF-20261127 queue (고컴): gamma / C sensitivity, n=1 per policy (user decision 2026-11-27: "각 1회").
# smoke 120 s for the 5 new modules (revF-v4 reuses the already-smoked revC-v4.ko), check-run on each smoke, then
# queue-order.registered.txt (pre-registered order/seed). After every run: check-run.py (anomaly -> stop, next run NOT started)
# and sync-push.sh (between measurements). Never touches nvme0n1 (safety-env.sh).
C=/home/oy/iCAT/result/revF-20261127; J=/home/oy/iCAT/EXPERIMENT_LOG.md; L=$C/queue.log
echo $$ > $C/queue.pid
busy() { [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; }
busy && { echo "$(date -Is) device occupied; revF NOT started" >> $L; exit 1; }
setsid nohup $C/loadsampler.sh > /dev/null 2>&1 < /dev/null &
echo "$(date -Is) revF starts" >> $L
printf -- '\n### revF-20261127 queue started %s: smokes g90 c075 g99 g95 c050, then 6 runs n=1 (queue-order.registered.txt)\n' "$(date -Is)" >> $J
for pol in revF-g90 revF-c075 revF-g99 revF-g95 revF-c050; do
  echo "$(date -Is) start smoke $pol" >> $L
  $C/run-one.sh "$pol" 1 smoke; rc=$?
  echo "$(date -Is) end smoke $pol exit=$rc" >> $L
  printf -- '- revF-20261127 smoke %s finished %s exit=%s, evidence `%s`\n' "$pol" "$(date -Is)" "$rc" "$C/raw/mixFYF-$pol-rep1-smoke120" >> $J
  python3 -I $C/check-run.py $C/raw/mixFYF-$pol-rep1-smoke120 >> $L 2>&1; ck=$?
  if (( rc != 0 || ck != 0 )) || busy; then echo "$(date -Is) ANOMALY smoke $pol (exit=$rc check=$ck); main queue NOT started" >> $L; $C/sync-push.sh; exit 1; fi
done
echo "$(date -Is) all 5 smokes passed; main queue starts" >> $L; $C/sync-push.sh
while read -r pol rep; do
  [[ -e $C/raw/mixFYF-$pol-rep$rep ]] && { echo "$(date -Is) skip existing $pol rep$rep" >> $L; continue; }
  echo "$(date -Is) start $pol rep$rep" >> $L
  $C/run-one.sh "$pol" "$rep"; rc=$?
  echo "$(date -Is) end $pol rep$rep exit=$rc" >> $L
  printf -- '- revF-20261127 %s rep%s finished %s exit=%s, evidence `%s`\n' "$pol" "$rep" "$(date -Is)" "$rc" "$C/raw/mixFYF-$pol-rep$rep" >> $J
  python3 -I $C/check-run.py $C/raw/mixFYF-$pol-rep$rep >> $L 2>&1; ck=$?
  $C/sync-push.sh "mixFYF-$pol-rep$rep"
  if (( rc != 0 || ck != 0 )) || busy; then
    echo "$(date -Is) ANOMALY after $pol rep$rep (exit=$rc check=$ck); queue stopped, next run NOT started" >> $L
    printf -- '- revF-20261127 queue stopped after %s rep%s: exit=%s check=%s (see checks.tsv)\n' "$pol" "$rep" "$rc" "$ck" >> $J
    exit 1
  fi
done < $C/queue-order.registered.txt
echo "$(date -Is) main queue finished" >> $L; kill "$(cat $C/loadsampler.pid)" 2>/dev/null; $C/sync-push.sh
