#!/usr/bin/env bash
# 10-04 (user): a 10 h transition workload where the candidate set visibly narrows: FIO-Fast -> Varmail.
# FIO-Fast 5 h (MULT=30: phase A was exactly 30 min at x3) + Varmail 5 h (VM_RUN=900 x VM_CHUNKS=20 -> one 18000 s run; varmail has no leak).
# This PC: iCAT-v4 then CAT-50 (robust). CAT-37 (default) runs on the second PC with the same command.
# Then the paused work: queue31 remainder, FIO-Fast 3 h CAT-37, and finally QUEUE34DONE so queue32 can start.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
free() { until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done; }
tools() { fio --version >/dev/null 2>&1 && sqlite3 --version >/dev/null 2>&1 && java -version >/dev/null 2>&1; }
push() { git add -A >/dev/null 2>&1; git commit -qm "10h mixes: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; free
  if [[ -d $R/$d ]]; then t=$(date +%Y%m%d%H%M%S); mv $R/$d $R/$d-failed-$t; mv $R/$d.console.txt $R/$d-failed-$t.console.txt 2>/dev/null; fi
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; tools || { echo "tools broken before $d, skipped"; return; }
  "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"
  tools || { echo "SUSPECT $d: tools broken right after this run" | tee -a $R/$d/SUSPECT.txt; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; }; }
for p in onlinev4 fixed50; do run mixF-$p-rep1-x30 env MULT=30 VM_RUN=900 VM_CHUNKS=20 bash script/mix-20260911.sh mixF $p 1; push "mixF 10h $p"; done
bash script/gh-queue31-screen-confirm.sh
run t4-fixed37-rep1-x18 env MULT=18 bash script/mix-20260911.sh t4 fixed37 1; push "FIO-Fast 3h CAT-37 (default) for the long-run figure"
echo QUEUE34DONE $(date -Is) >> $S/queue34.out
