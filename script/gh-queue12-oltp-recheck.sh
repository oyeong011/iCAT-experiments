#!/usr/bin/env bash
# 거래 DB 흉내(oltp): 60-arm sweep said ratio 7 beats ratio 16 by 10% (arm46 1.332 vs arm50 1.471), 1 run each. Recheck x3 before trusting it. Starts after queue10.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE10DONE $S/queue10.out 2>/dev/null; do sleep 300; done
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "oltp recheck: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
for rep in 1 2 3; do for a in arm46 arm47 arm49 arm50; do
  f=result/filebench/oltp-$a-rep$rep.console.txt; [[ -e $f ]] && continue
  FILEBENCH_RUNTIME=300 bash script/gh-filebench.sh $a oltp > $f 2>&1 || echo "FAIL oltp $a rep$rep"
done; done; push "arm46/47/49/50 x3"
grep -H '^\[WAF\]' result/filebench/oltp-arm4[679]-rep*.console.txt result/filebench/oltp-arm50-rep*.console.txt
echo QUEUE12DONE $(date -Is)
