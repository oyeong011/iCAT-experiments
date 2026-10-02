#!/usr/bin/env bash
# 2026-10-02: 10-hour transition workloads, CAT-47 (best) vs CAT-50 (robust) vs iCAT-v4. After queue31, before queue32.
# OLTP->Varmail only (user, 10-02): MULT=20 VM_RUN=18000 = two 5 h filebench phases, ~10 h per run. D and J dropped.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
# 10-02 23:55 (user): top priority — no longer waits for queue31; queue31 resumes after the 10 h runs (below)
free() { until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done; }
tools() { fio --version >/dev/null 2>&1 && sqlite3 --version >/dev/null 2>&1 && java -version >/dev/null 2>&1; }
push() { git add -A >/dev/null 2>&1; git commit -qm "10h mixes: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; free
  if [[ -d $R/$d ]]; then t=$(date +%Y%m%d%H%M%S); mv $R/$d $R/$d-failed-$t; mv $R/$d.console.txt $R/$d-failed-$t.console.txt 2>/dev/null; fi
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; tools || { echo "tools broken before $d, skipped"; return; }
  "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"
  tools || { echo "SUSPECT $d: tools broken right after this run" | tee -a $R/$d/SUSPECT.txt; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; }; }
# 10-02 (user): OLTP->Varmail 10 h, v4 and CAT-50 (robust) only. CAT-37 (default) runs on the second PC; CAT-47 not needed.
for p in onlinev4 fixed50; do run mixO-$p-rep1-x20 env MULT=20 VM_RUN=18000 bash script/mix-20260911.sh mixO $p 1; push "mixO 10h $p"; done
bash script/gh-queue31-screen-confirm.sh   # finish the paused screen/confirm (done runs are skipped)
run t4-fixed37-rep1-x18 env MULT=18 bash script/mix-20260911.sh t4 fixed37 1; push "FIO-Fast 3h CAT-37 (default) for the long-run figure"
echo QUEUE34DONE $(date -Is)
