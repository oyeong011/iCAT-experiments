#!/usr/bin/env bash
# mixR with the default CAT (arm37) so every learner version can be compared with the default. After queue15, before queue10.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE15DONE $S/queue15.out 2>/dev/null; do sleep 120; done
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
R=result/mix-20260911; d=mixR-fixed37-rep1-x3
[[ -e $R/$d/summary.txt ]] || { rm -rf $R/$d; MULT=3 bash script/mix-20260911.sh mixR fixed37 1 > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
git add -A >/dev/null 2>&1; git commit -qm "mixR: fixed37 x3" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] mixR fixed37 $(date -Is)"
echo QUEUE17DONE $(date -Is)
