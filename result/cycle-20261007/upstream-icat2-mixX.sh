#!/usr/bin/env bash
# For the SECOND PC (Codex), 10-07: cycle mix mixX — CAT-50 (robust) then CAT-37 (default). This PC runs iCAT-v6 then CAT-47.
# mixX = (FIO-Fast, Varmail, OLTP, FIO-Fast, OLTP, Varmail) x 3 + (FIO-Fast, Varmail), 20 phases x 1800 s = 10 h, Table-3 prep (6 GiB FIO file kept), no YCSB.
# Pre-registered in EXPERIMENT_LOG.md ("주기 혼합(mixX) — 사전 등록 2026-10-07").  Usage: bash script/icat2-mixX.sh
set -euo pipefail
cd ~/iCAT
R=result/cycle-20261007
ok() { [[ $(cat $1/exit-code.txt 2>/dev/null) == 0 && $(grep -c '^phaseS[0-9]*(' $1/summary.txt 2>/dev/null) -ge 20 ]]; }
for p in fixed50 fixed37; do
  env PH_SECS=60 MIX_BASE=$PWD/$R/fitcheck bash script/mix-cycle-20261007.sh mixX $p 1
  ok $R/fitcheck/mixX-$p-rep1 || { echo "mixX $p short check failed"; exit 1; }
  env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX $p 1
done
