#!/usr/bin/env bash
# queue46 (10-06 21:35): mixV with a 5 GiB FIO-Fast (cold region 3 GiB; user) and the 600k DB. One full-size check at 5 min per
# phase (runner exits 3 on any YCSB Return=ERROR), then iCAT-v4 10 h, then CAT-47 10 h.
# Launched with "hold=script/sqlite.sh".
cd /home/oy/iCAT; R=result/inherit-20261006
push() { git add $R script/mix-inherit-20261006.sh script/gh-queue46-mixV.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "mixV: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
wait_dev() { until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; }
N=
for n in 600000; do
  F=$R/fitcheck-fio5g-$n; mkdir -p $F; wait_dev; echo "fit $n $(date -Is)"
  env MIXV_FIO_GB=5 MIXV_RECORDS=$n PH_SECS=300 MIX_BASE=$PWD/$F bash script/mix-inherit-20261006.sh mixV onlinev4 1 > $F/mixV-onlinev4-rep1.console.txt 2>&1
  if [[ $(cat $F/mixV-onlinev4-rep1/exit-code.txt 2>/dev/null) == 0 && $(grep -c '^phase[A-I](' $F/mixV-onlinev4-rep1/summary.txt 2>/dev/null) -ge 9 ]]; then N=$n; push "fit check $n passed"; break; fi
  push "fit check $n failed"
done
[[ -n $N ]] || { echo "NO SIZE FITS"; sleep 86400; exit 1; }
echo $N > $R/chosen-records.txt
for p in onlinev4 fixed47; do
  wait_dev; echo "start 10h $p records=$N $(date -Is)"
  env MIXV_FIO_GB=5 MIXV_RECORDS=$N PH_SECS=4000 bash script/mix-inherit-20261006.sh mixV $p 1 > $R/mixV-$p-rep1.console.txt 2>&1 || echo "FAIL $p"
  push "10h $p records=$N"
done
echo QUEUE45DONE $(date -Is); sleep 86400
