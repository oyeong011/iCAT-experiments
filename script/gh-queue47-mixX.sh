#!/usr/bin/env bash
# queue47 (10-07): cycle mix mixX on this PC after the running mixV CAT-47 10 h: short full-size check (60 s phases) with v6,
# then iCAT-v6 10 h, then CAT-47 10 h. Launched with "hold=script/sqlite.sh" so the older queues keep waiting.
cd /home/oy/iCAT; R=result/cycle-20261007; F=$R/fitcheck; mkdir -p $F
until [[ -f result/inherit-20261006/mixV-fixed47-rep1/exit-code.txt ]] && [[ ! -e /sys/module/nvmev ]]; do sleep 20; done
pkill -f "gh-queue46-mixV.sh" 2>/dev/null
push() { git add $R result/inherit-20261006/mixV-fixed47-rep1 script/mix-cycle-20261007.sh script/gh-queue47-mixX.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "mixX: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
push "mixV CAT-47 10h done"
wait_dev() { until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; }
wait_dev; echo "check $(date -Is)"
env PH_SECS=60 MIX_BASE=$PWD/$F bash script/mix-cycle-20261007.sh mixX onlinev6 1 > $F/mixX-onlinev6-rep1.console.txt 2>&1
if [[ $(cat $F/mixX-onlinev6-rep1/exit-code.txt 2>/dev/null) != 0 || $(grep -c '^phaseS[0-9]*(' $F/mixX-onlinev6-rep1/summary.txt 2>/dev/null) -lt 20 ]]; then
  echo "CHECK FAILED"; push "short check FAILED"; sleep 86400; exit 1; fi
push "short check passed"
for p in onlinev6 fixed47; do
  wait_dev; echo "start 10h $p $(date -Is)"
  env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX $p 1 > $R/mixX-$p-rep1.console.txt 2>&1 || echo "FAIL $p"
  push "10h $p"
done
echo QUEUE47DONE $(date -Is); sleep 86400
