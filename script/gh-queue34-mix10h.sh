#!/usr/bin/env bash
# 2026-10-02: 10-hour transition workloads, CAT-47 (best) vs CAT-50 (robust) vs iCAT-v4. After queue31, before queue32.
# OLTP->Varmail only (user, 10-02): MULT=20 VM_RUN=18000 = two 5 h filebench phases, ~10 h per run. D and J dropped.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE31DONE $S/queue31.out 2>/dev/null; do sleep 300; done
free() { until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done; }
tools() { fio --version >/dev/null 2>&1 && sqlite3 --version >/dev/null 2>&1 && java -version >/dev/null 2>&1; }
push() { git add -A >/dev/null 2>&1; git commit -qm "10h mixes: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; free
  if [[ -d $R/$d ]]; then t=$(date +%Y%m%d%H%M%S); mv $R/$d $R/$d-failed-$t; mv $R/$d.console.txt $R/$d-failed-$t.console.txt 2>/dev/null; fi
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; tools || { echo "tools broken before $d, skipped"; return; }
  "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"
  tools || { echo "SUSPECT $d: tools broken right after this run" | tee -a $R/$d/SUSPECT.txt; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; }; }
# 10-02 (user): one workload only — OLTP->Varmail 10 h. v4 vs CAT-50 (robust) vs CAT-37 (default) first; CAT-47 last (for the results table).
for p in onlinev4 fixed50 fixed37 fixed47; do run mixO-$p-rep1-x20 env MULT=20 VM_RUN=18000 bash script/mix-20260911.sh mixO $p 1; push "mixO 10h $p"; done
run t4-fixed37-rep1-x18 env MULT=18 bash script/mix-20260911.sh t4 fixed37 1; push "FIO-Fast 3h CAT-37 (default) for the long-run figure"
echo QUEUE34DONE $(date -Is)
