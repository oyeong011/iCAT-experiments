#!/usr/bin/env bash
# 2026-09-28: after queue23, repeat v4 x3 on the four app mixes where v4 beat robust CAT once, then regenerate all tables.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE23DONE $S/queue23.out 2>/dev/null; do sleep 120; done
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "confirm: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d; "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
for lb in mixO mixF mixP mixJ; do run $lb-onlinev4-rep2-x3 env MULT=3 VM_RUN=900 bash script/mix-20260911.sh $lb onlinev4 2; push "$lb v4 x3 rep2"; done
python3 analysis/all-tables.py > /dev/null 2>&1; push "RESULTS_ALL regenerated"
echo QUEUE24DONE $(date -Is)
