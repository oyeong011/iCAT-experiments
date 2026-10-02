#!/usr/bin/env bash
# After every queue: gather all new results into one file, copy queue logs into the repo, commit and push.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE18DONE $S/queue18.out 2>/dev/null; do sleep 600; done
O=result/final-20260929; mkdir -p $O
cp $S/queue1[0-8].out $O/ 2>/dev/null
{
  echo "# 자동 정리 $(date -Is)"; echo
  echo "## 모든 명시 계측 run (전체 WAF / 구간별)"
  for f in result/mix-20260911/*/summary.txt; do d=$(basename $(dirname $f))
    case $d in mixR-*|*-x18|*-x60|t4long-*|t4-onlinev[34]*|*-x3|*-x6) ;; *) continue;; esac
    printf '%-32s %s\n' "$d" "$(grep -E '^total|^phase[ABC]\(' $f | sed 's/ gc_pages=[0-9]*//;s/host_bytes=[0-9]* //;s/host_pages=[0-9]* //' | tr '\n' ' ')"
  done; echo
  echo "## 아주 느린 3영역 60조합 순위"; cat result/sweep-slow16-20260921/rank-slow16.txt 2>/dev/null; echo
  echo "## 거래 DB 흉내 재확인 (arm46/47/49/50 x3)"; grep -H '^\[WAF\]' result/filebench/oltp-arm4[679]-rep*.console.txt result/filebench/oltp-arm50-rep*.console.txt 2>/dev/null
} > $O/ALL-NEW-RESULTS.md
python3 analysis/summary.py > $O/summary-table.txt 2>&1
git add -A >/dev/null 2>&1; git commit -qm "final: all queues done, results gathered in result/final-20260929" >/dev/null 2>&1
for i in 1 2 3 4 5; do git push -q 2>/dev/null && break; sleep 120; done
echo QUEUE19DONE $(date -Is)
