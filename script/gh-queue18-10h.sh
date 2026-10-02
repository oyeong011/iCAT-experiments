#!/usr/bin/env bash
# 10-hour fast 3-region writes (MULT=60): v4 then v3. Real workloads run for hours; checks the extrapolated plateau (v3 ~1.83). After queue16.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE16DONE $S/queue16.out 2>/dev/null; do sleep 300; done
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
R=result/mix-20260911
for p in onlinev4 onlinev3; do d=t4-$p-rep1-x60
  [[ -e $R/$d/summary.txt ]] || { rm -rf $R/$d; MULT=60 bash script/mix-20260911.sh t4 $p 1 > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
  git add -A >/dev/null 2>&1; git commit -qm "10h: $d" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $d $(date -Is)"
done
echo QUEUE18DONE $(date -Is)
