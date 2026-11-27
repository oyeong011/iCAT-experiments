#!/usr/bin/env bash
# revG-20261128 queue (고컴, 16 GiB): started by boot-start.sh after the reboot into memmap=16G$4G.
# smoke 120 s (FIO phases 240 s) for revG-v4 and revG-random, check-run on each, then queue-order.registered.txt (pre-registered
# order/seeds). After every run: check-run.py (anomaly -> stop, next run NOT started) and sync-push.sh. Never touches nvme0n1.
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin HOME=/home/oy
C=/home/oy/iCAT/result/revG-20261128; J=/home/oy/iCAT/EXPERIMENT_LOG.md; L=$C/queue.log
echo $$ > $C/queue.pid
busy() { [[ -e /sys/module/nvmev ]] || mountpoint -q /home/oy/iCAT/mnt; }
busy && { echo "$(date -Is) device occupied; revG NOT started" >> $L; exit 1; }
setsid nohup $C/loadsampler.sh > /dev/null 2>&1 < /dev/null &
echo "$(date -Is) revG starts" >> $L
printf -- '\n### revG-20261128 queue started %s (16 GiB, after reboot): smokes revG-v4 revG-random, then 6 runs (queue-order.registered.txt)\n' "$(date -Is)" >> $J
for pol in revG-v4 revG-random; do
  echo "$(date -Is) start smoke $pol" >> $L
  $C/run-one.sh "$pol" 1 smoke; rc=$?
  echo "$(date -Is) end smoke $pol exit=$rc" >> $L
  printf -- '- revG-20261128 smoke %s finished %s exit=%s, evidence `%s`\n' "$pol" "$(date -Is)" "$rc" "$C/raw/mixFYF-$pol-rep1-smoke120" >> $J
  python3 -I $C/check-run.py $C/raw/mixFYF-$pol-rep1-smoke120 >> $L 2>&1; ck=$?
  if (( rc != 0 || ck != 0 )) || busy; then echo "$(date -Is) ANOMALY smoke $pol (exit=$rc check=$ck); main queue NOT started" >> $L; $C/sync-push.sh; exit 1; fi
done
echo "$(date -Is) both smokes passed; main queue starts" >> $L; $C/sync-push.sh
while read -r pol rep; do
  [[ -e $C/raw/mixFYF-$pol-rep$rep ]] && { echo "$(date -Is) skip existing $pol rep$rep" >> $L; continue; }
  echo "$(date -Is) start $pol rep$rep" >> $L
  $C/run-one.sh "$pol" "$rep"; rc=$?
  echo "$(date -Is) end $pol rep$rep exit=$rc" >> $L
  printf -- '- revG-20261128 %s rep%s finished %s exit=%s, evidence `%s`\n' "$pol" "$rep" "$(date -Is)" "$rc" "$C/raw/mixFYF-$pol-rep$rep" >> $J
  python3 -I $C/check-run.py $C/raw/mixFYF-$pol-rep$rep >> $L 2>&1; ck=$?
  $C/sync-push.sh "mixFYF-$pol-rep$rep"
  if (( rc != 0 || ck != 0 )) || busy; then
    echo "$(date -Is) ANOMALY after $pol rep$rep (exit=$rc check=$ck); queue stopped, next run NOT started" >> $L
    printf -- '- revG-20261128 queue stopped after %s rep%s: exit=%s check=%s (see checks.tsv)\n' "$pol" "$rep" "$rc" "$ck" >> $J
    exit 1
  fi
done < $C/queue-order.registered.txt
echo "$(date -Is) main queue finished" >> $L; kill "$(cat $C/loadsampler.pid)" 2>/dev/null; $C/sync-push.sh
