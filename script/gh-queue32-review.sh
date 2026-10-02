#!/usr/bin/env bash
# 2026-10-01: experiments requested by the first-time reviewer. After queue31.
# A. iCAT-v4 to n=3 on all 13 transition workloads (x3)   B. fixed-arm repeats on OLTP->Varmail (the only "beats all fixed" case)
# C. ablations: v3 components (window, sweep visits, drift threshold), v4 mechanisms (elimination, neighbour probe, partial reset), repeats.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE31DONE $S/queue31.out 2>/dev/null; do sleep 300; done
free() { until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done; }
tools() { fio --version >/dev/null 2>&1 && sqlite3 --version >/dev/null 2>&1 && java -version >/dev/null 2>&1; }
push() { git add -A >/dev/null 2>&1; git commit -qm "review: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; free; rm -rf $R/$d
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; tools || { echo "tools broken before $d, skipped"; return; }
  "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"
  tools || { echo "SUSPECT $d" | tee -a $R/$d/SUSPECT.txt; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; }; }
X3="env MULT=3 VM_RUN=900 bash script/mix-20260911.sh"
for rep in 2 3; do for lb in mixA mixB mixC mixD mixF mixG mixH mixJ mixK mixL mixO mixP mixQ; do run $lb-onlinev4-rep$rep-x3 $X3 $lb onlinev4 $rep; done; push "v4 x3 rep$rep all mixes"; done
for p in fixed47 arm17 fixed50; do for rep in 2 3; do run mixO-$p-rep$rep-x3 $X3 mixO $p $rep; done; done; push "OLTP->Varmail fixed repeats"
X18="env MULT=18 bash script/mix-20260911.sh t4"
run t4-onlinev4-rep1-x18 $X18 onlinev4 1
for p in onlinev3win1 onlinev3visits3 onlinev3drift12 onlinev4noelim onlinev4noprobe; do run t4-$p-rep1-x18 $X18 $p 1; push "ablation $p"; done
run mixR-onlinev4fullreset-rep1-x3 env MULT=3 bash script/mix-20260911.sh mixR onlinev4fullreset 1; push "ablation v4 full reset (3-phase)"
for p in onlinev3 onlinev3k2 onlinev3probe; do run t4-$p-rep2-x18 $X18 $p 2; done; push "ablation repeats"
python3 analysis/all-tables.py >/dev/null 2>&1; python3 analysis/figures.py >/dev/null 2>&1; python3 analysis/v4-vs-cat.py >/dev/null 2>&1; python3 analysis/all-runs.py >/dev/null 2>&1; bash analysis/dashboard-build.sh >/dev/null 2>&1; push "tables, figures, board regenerated"
echo QUEUE32DONE $(date -Is)
