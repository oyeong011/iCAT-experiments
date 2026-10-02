#!/usr/bin/env bash
# mixR = 빠른 3영역 → SQLite 읽기50/수정50 → 빠른 3영역, equal host writes per phase, x3 length (~2.5 h). After queue14 (v3), before queue10.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE14DONE $S/queue14.out 2>/dev/null; do sleep 300; done
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "mixR: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d; "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
run mixR-fixed47-rep1-smoke env SMOKE=1 bash script/mix-20260911.sh mixR fixed47 1
[[ -e $R/mixR-fixed47-rep1-smoke/summary.txt ]] || { echo "SMOKE FAIL, skipping mixR"; echo QUEUE15DONE $(date -Is); exit; }
push "smoke"
run t4-onlinev4-rep1-smoke env SMOKE=1 bash script/mix-20260911.sh t4 onlinev4 1
[[ -e $R/t4-onlinev4-rep1-smoke/summary.txt ]] && push "v4 smoke" || echo "V4 SMOKE FAIL"
for p in onlinev4 onlinev3 arm32 fixed47 arm17 fixed50 online greedy; do run mixR-$p-rep1-x3 env MULT=3 bash script/mix-20260911.sh mixR $p 1; push "$p x3"; done
echo QUEUE15DONE $(date -Is)
