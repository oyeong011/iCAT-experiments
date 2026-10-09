#!/usr/bin/env bash
# queue51 (10-10): after the screening (queue50), build mixY from the GC-heavy workloads by the pre-registered rule, then on this PC:
# full-size short check (60 s phases, v6) -> iCAT-v6 10 h -> CAT-47 10 h. The second PC runs CAT-50 and CAT-37 (script/icat2-mixY.sh)
# from the committed result/gc-20261010/mixy-seq.txt. Launched with "hold=script/sqlite.sh".
cd /home/oy/iCAT; R=result/gc-20261010; S=result/screen-20261008; mkdir -p $R
until grep -q QUEUE50DONE result/queue50.out 2>/dev/null; do sleep 60; done
pkill -f "gh-queue50-screen.sh" 2>/dev/null
waf() { grep 'phaseA(' $S/$1/summary.txt 2>/dev/null | sed 's/.*WAF=//'; }
ok() { [[ $(cat $S/$1/exit-code.txt 2>/dev/null) == 0 ]] && python3 -c "import sys; sys.exit(0 if float('$(waf $1)' or 0) >= 1.2 else 1)" 2>/dev/null; }
L="F S V"; ok scrWP-fixed47 && L="$L P"; ok scrFS-fixed47 && L="$L W"
SEQ=$(python3 analysis/mixy-seq.py $L); echo "$SEQ" > $R/mixy-seq.txt
{ echo "- $(date -Is) mixY 구성 결정(사전 등록 규칙): 선별 WAF webproxy(CAT-47)=$(waf scrWP-fixed47) / CAT-37=$(waf scrWP-fixed37), fileserver(CAT-47)=$(waf scrFS-fixed47) / CAT-37=$(waf scrFS-fixed37) → 워크로드 [$L], 순서 \`$SEQ\` (\`$R/mixy-seq.txt\`)."; } >> EXPERIMENT_LOG.md
push() { git add $R $S analysis/mixy-seq.py script/mix-gc-20261010.sh script/gh-queue51-mixY.sh script/icat2-mixY.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "mixY: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
push "composition decided: $SEQ"
wait_dev() { until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; }
wait_dev; mkdir -p $R/fitcheck; echo "check $(date -Is)"
env MIXY_SEQ="$SEQ" PH_SECS=60 MIX_BASE=$PWD/$R/fitcheck bash script/mix-gc-20261010.sh mixY onlinev6 1 > $R/fitcheck/mixY-onlinev6-rep1.console.txt 2>&1
if [[ $(cat $R/fitcheck/mixY-onlinev6-rep1/exit-code.txt 2>/dev/null) != 0 || $(grep -c '^phaseS[0-9]*(' $R/fitcheck/mixY-onlinev6-rep1/summary.txt 2>/dev/null) -lt 20 ]]; then
  echo "CHECK FAILED"; push "short check FAILED"; sleep 86400; exit 1; fi
push "short check passed"
for p in onlinev6 fixed47; do
  wait_dev; echo "start 10h $p $(date -Is)"
  env MIXY_SEQ="$SEQ" PH_SECS=1800 bash script/mix-gc-20261010.sh mixY $p 1 > $R/mixY-$p-rep1.console.txt 2>&1 || echo "FAIL $p"
  push "10h $p"
done
echo QUEUE51DONE $(date -Is); sleep 86400
