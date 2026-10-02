#!/usr/bin/env bash
# 2026-09-27 21:45: the 14 mix designs are ~10-30 min at x1 — shorter than v4's 15-min sweep. Re-run at x3 length.
# v4 first on 13 mixes (mixM ramp steps are fixed 120 s and cannot be stretched), then robust CAT (fixed50) at x3 for the same mixes.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
free() { until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done; }
free
push() { git add -A >/dev/null 2>&1; git commit -qm "mixes x3: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d; "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
MIXES="mixA mixC mixB mixD mixJ mixK mixH mixF mixG mixL mixO mixP mixQ"
for lb in $MIXES; do run $lb-onlinev4-rep1-x3 env MULT=3 VM_RUN=900 bash script/mix-20260911.sh $lb onlinev4 1; push "$lb v4"; done
echo V4X3DONE $(date -Is)
for lb in $MIXES; do run $lb-fixed50-rep1-x3 env MULT=3 VM_RUN=900 bash script/mix-20260911.sh $lb fixed50 1; push "$lb fixed50"; done
echo F50X3DONE $(date -Is)
for lb in $MIXES; do run $lb-fixed47-rep1-x3 env MULT=3 VM_RUN=900 bash script/mix-20260911.sh $lb fixed47 1; push "$lb fixed47"; done
echo QUEUE22DONE $(date -Is)
