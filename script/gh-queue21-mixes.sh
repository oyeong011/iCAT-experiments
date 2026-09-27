#!/usr/bin/env bash
# 2026-09-27: evaluate v4 (then v3) on every mix design. Replaces queue20's tail.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
free() { until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done; }
free
push() { git add -A >/dev/null 2>&1; git commit -qm "mixes: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; rm -rf $R/$d; "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"; }
MIXES="mixA mixB mixC mixD mixF mixG mixH mixJ mixK mixL mixM mixO mixP mixQ"
# 1. finish oltp recheck (skips files that exist)
for rep in 1 2 3; do for a in arm46 arm47 arm49 arm50; do f=result/filebench/oltp-$a-rep$rep.console.txt; [[ -e $f ]] && continue
  FILEBENCH_RUNTIME=300 bash script/gh-filebench.sh $a oltp > $f 2>&1 || echo "FAIL oltp $a rep$rep"; done; done; push "oltp recheck"
# 2. new mix seed 2: v4 and robust CAT
for p in onlinev4 fixed50; do run mixR-$p-rep2-x3 env MULT=3 bash script/mix-20260911.sh mixR $p 2; done; push "mixR rep2"
# 3. v4 on all 14 mixes (x1, seed 1) — v1/fixed/greedy already have 3 seeds
for lb in $MIXES; do run $lb-onlinev4-rep1 bash script/mix-20260911.sh $lb onlinev4 1; done; push "v4 x 14 mixes"
# 4. v4 on the x3 mixes that already have fixed47/fixed50/v1/v2 at x3
for lb in mixA mixC; do run $lb-onlinev4-rep1-x3 env MULT=3 bash script/mix-20260911.sh $lb onlinev4 1; done; push "v4 x3 mixA/mixC"
echo MIXESV4DONE $(date -Is)
# 5. slow sweep (skips arms already done)
bash script/gh-queue10-slow16.sh
# 6. v3 on all 14 mixes
for lb in $MIXES; do run $lb-onlinev3-rep1 bash script/mix-20260911.sh $lb onlinev3 1; done; push "v3 x 14 mixes"
# final gather
O=result/final-20260929; mkdir -p $O; cp $S/queue*.out $O/ 2>/dev/null
{ echo "# 자동 정리 $(date -Is)"; echo
  for f in $R/*/summary.txt; do d=$(basename $(dirname $f)); case $d in *onlinev[34]*|mixR-*|*-x18|*-x60|t4long-*|*-x3|*-x6) ;; *) continue;; esac
    printf '%-32s %s\n' "$d" "$(grep -E '^total|^phase[ABC]\(' $f | sed 's/ gc_pages=[0-9]*//;s/host_bytes=[0-9]* //;s/host_pages=[0-9]* //' | tr '\n' ' ')"; done; echo
  echo "## 아주 느린 3영역 60조합 순위"; cat result/sweep-slow16-20260921/rank-slow16.txt 2>/dev/null; echo
  echo "## 거래 DB 흉내 재확인"; grep -H '^\[WAF\]' result/filebench/oltp-arm4[679]-rep*.console.txt result/filebench/oltp-arm50-rep*.console.txt 2>/dev/null
} > $O/ALL-NEW-RESULTS.md
push "final gather"
echo QUEUE21DONE $(date -Is)
