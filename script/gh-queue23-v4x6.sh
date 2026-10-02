#!/usr/bin/env bash
# 2026-09-28: finish robust CAT at x3, then v4 at x6 on the four mixes that already have fixed47/fixed50/v1/v2/v3 at x6. fixed47 x3 cancelled (x1 values used; fixed arms are length-invariant).
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
free() { until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done; }
free
push() { git add -A >/dev/null 2>&1; git commit -qm "v4 long mixes: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d; "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
for lb in mixF mixG mixL mixO mixP mixQ; do run $lb-fixed50-rep1-x3 env MULT=3 VM_RUN=900 bash script/mix-20260911.sh $lb fixed50 1; push "$lb fixed50 x3"; done
for lb in mixA mixC mixD mixK; do run $lb-onlinev4-rep1-x6 env MULT=6 bash script/mix-20260911.sh $lb onlinev4 1; push "$lb v4 x6"; done
echo QUEUE23DONE $(date -Is)
