#!/usr/bin/env bash
# queue40 (10-06): inheritance mix (mixV) — v4 then CAT-47, smoke first. Pre-registered in EXPERIMENT_LOG.md.
# Launched as `bash script/gh-queue40-inherit.sh hold=script/sqlite.sh`: that argument makes the older queues' free()
# pgrep match this queue, so they wait until it is done instead of grabbing the device between our runs.
cd /home/oy/iCAT
R=result/inherit-20261006; mkdir -p $R
wait_dev() { until ! pgrep -f "mix-20260911.sh mixT onlinev6" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; }
push() { git add $R script/mix-inherit-20261006.sh script/gh-queue40-inherit.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "inherit: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
smoke_ok() { local d=$R/$1; [[ $(cat $d/exit-code.txt 2>/dev/null) == 0 && $(grep -c '^phase[A-I](' $d/summary.txt 2>/dev/null) -ge 9 ]] \
  && ls $d/extents-*.txt >/dev/null 2>&1 && ! grep -qi 'no space left\|ENOSPC' $d/*.txt 2>/dev/null; }
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; wait_dev
  [[ -d $R/$d ]] && mv $R/$d $R/$d-failed-$(date +%Y%m%d%H%M%S)
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
  echo "start $d $(date -Is)"; "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
for p in onlinev4 fixed47; do   # 10-06 user: v4 first (CAT-47 smoke already passed; its 10 h restarts after v4)
  run mixV-$p-rep1-smoke env SMOKE=1 PH_SECS=120 bash script/mix-inherit-20261006.sh mixV $p 1
  if ! smoke_ok mixV-$p-rep1-smoke; then echo "SMOKE FAILED $p — stopping"; push "mixV $p smoke FAILED"; exit 1; fi
  push "mixV $p smoke passed"
  run mixV-$p-rep1 env PH_SECS=4000 bash script/mix-inherit-20261006.sh mixV $p 1; push "mixV 10h $p"
done
echo QUEUE40DONE $(date -Is)
