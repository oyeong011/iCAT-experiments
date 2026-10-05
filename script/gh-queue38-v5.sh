#!/usr/bin/env bash
# 10-05 (user): after the current mixT CAT-47 run, iCAT-v5 on the same irregular 10 h mix (mixT).
# v5 = v4 + GC-capped windows (>= 64 MiB host) are evaluated instead of discarded. Smoke first (120 s/phase).
# Replaces queue37's remaining CAT-50 backup (the second PC has CAT-50). Then the paused work, then QUEUE34DONE.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
free() { until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done; }
tools() { fio --version >/dev/null 2>&1 && sqlite3 --version >/dev/null 2>&1 && java -version >/dev/null 2>&1; }
push() { git add -A >/dev/null 2>&1; git commit -qm "v5: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; free
  if [[ -d $R/$d ]]; then t=$(date +%Y%m%d%H%M%S); mv $R/$d $R/$d-failed-$t; mv $R/$d.console.txt $R/$d-failed-$t.console.txt 2>/dev/null; fi
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; tools || { echo "tools broken before $d, skipped"; return; }
  "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"
  tools || { echo "SUSPECT $d: tools broken right after this run" | tee -a $R/$d/SUSPECT.txt; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; }; }
run mixT-onlinev5-rep1-smoke env SMOKE=1 PH_SECS=120 bash script/mix-20260911.sh mixT onlinev5 1
if [[ $(grep -c '^phase' $R/mixT-onlinev5-rep1-smoke/summary.txt 2>/dev/null) -lt 9 ]]; then echo "V5 SMOKE FAILED — stopping"; push "mixT v5 smoke FAILED"; exit 1; fi
push "mixT v5 smoke passed"
run mixT-onlinev5-rep1 env PH_SECS=4000 bash script/mix-20260911.sh mixT onlinev5 1; push "mixT 10h onlinev5"
bash script/gh-queue31-screen-confirm.sh
run t4-fixed37-rep1-x18 env MULT=18 bash script/mix-20260911.sh t4 fixed37 1; push "FIO-Fast 3h CAT-37 (default) for the long-run figure"
echo QUEUE34DONE $(date -Is) >> $S/queue34.out
