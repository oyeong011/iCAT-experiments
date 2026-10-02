#!/usr/bin/env bash
# Month-end priority order (2026-09-27): key results first, then resume the slow sweep (it skips arms already done).
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
push() { git add -A >/dev/null 2>&1; git commit -qm "priority: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d; "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
# 1. v4 10 h
run t4-onlinev4-rep1-x60 env MULT=60 bash script/mix-20260911.sh t4 onlinev4 1; push "v4 10 h"
# 2. oltp recheck (arm46/47/49/50 x3)
for rep in 1 2 3; do for a in arm46 arm47 arm49 arm50; do f=result/filebench/oltp-$a-rep$rep.console.txt; [[ -e $f ]] && continue
  FILEBENCH_RUNTIME=300 bash script/gh-filebench.sh $a oltp > $f 2>&1 || echo "FAIL oltp $a rep$rep"; done; done; push "oltp recheck"
# 3. (dropped) v4 3 h: read from the 10 h run's 30 s counter series (control-series.txt) at t = 3 h
# 4. new mix seed 2: v4 and robust CAT
for p in onlinev4 fixed50; do run mixR-$p-rep2-x3 env MULT=3 bash script/mix-20260911.sh mixR $p 2; done; push "mixR rep2 v4 + fixed50"
echo PRIORITYDONE $(date -Is)
# 5. resume the slow sweep (skips arms whose console file exists)
bash script/gh-queue10-slow16.sh
# 6. v3 10 h if time remains
run t4-onlinev3-rep1-x60 env MULT=60 bash script/mix-20260911.sh t4 onlinev3 1; push "v3 10 h"
# final gather
O=result/final-20260929; mkdir -p $O; cp $S/queue*.out $O/ 2>/dev/null
{ echo "# 자동 정리 $(date -Is)"; echo
  for f in $R/*/summary.txt; do d=$(basename $(dirname $f)); case $d in mixR-*|*-x18|*-x60|t4long-*|t4-onlinev[34]*|*-x3|*-x6) ;; *) continue;; esac
    printf '%-32s %s\n' "$d" "$(grep -E '^total|^phase[ABC]\(' $f | sed 's/ gc_pages=[0-9]*//;s/host_bytes=[0-9]* //;s/host_pages=[0-9]* //' | tr '\n' ' ')"; done; echo
  echo "## 아주 느린 3영역 60조합 순위"; cat result/sweep-slow16-20260921/rank-slow16.txt 2>/dev/null; echo
  echo "## 거래 DB 흉내 재확인"; grep -H '^\[WAF\]' result/filebench/oltp-arm4[679]-rep*.console.txt result/filebench/oltp-arm50-rep*.console.txt 2>/dev/null
} > $O/ALL-NEW-RESULTS.md
push "final gather"
echo QUEUE20DONE $(date -Is)
