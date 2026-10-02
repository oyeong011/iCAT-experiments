#!/usr/bin/env bash
# 2026-09-29: third v4 run on oltp -> varmail (x3), the only mix where v4 beat all six fixed arms. After queue28.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE28DONE $S/queue28.out 2>/dev/null; do sleep 120; done
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
d=result/mix-20260911/mixO-onlinev4-rep3-x3
if [[ ! -e $d/summary.txt ]]; then rm -rf $d; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
  MULT=3 VM_RUN=900 bash script/mix-20260911.sh mixO onlinev4 3 > $d.console.txt 2>&1 || echo "FAIL $d"; fi
python3 analysis/all-tables.py > /dev/null 2>&1; python3 analysis/figures.py > /dev/null 2>&1
git add -A >/dev/null 2>&1; git commit -qm "mixO v4 rep3; tables and figures regenerated" >/dev/null 2>&1; git push -q 2>/dev/null
echo QUEUE29DONE $(date -Is)
