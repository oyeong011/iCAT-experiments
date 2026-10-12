#!/usr/bin/env bash
# For the SECOND PC (Codex), 10-10: GC-heavy mix mixY with CAT-50 then CAT-37 (this PC runs iCAT-v6 and CAT-47).
# The workload order is read from result/gc-20261010/mixy-seq.txt, which this PC commits after the screening — pull first.
# Pre-registered in EXPERIMENT_LOG.md ("GC 부담 혼합(mixY) — 사전 등록 2026-10-10"). Usage: bash script/icat2-mixY.sh
set -euo pipefail
cd ~/iCAT
R=result/gc-20261010; SEQ=$(cat $R/mixy-seq.txt); [[ $(wc -w <<<"$SEQ") == 20 ]] || { echo "mixy-seq.txt missing: pull after this PC decided"; exit 1; }
for p in fixed50 fixed37; do
  env MIXY_SEQ="$SEQ" PH_SECS=1800 bash script/mix-gc-20261010.sh mixY $p 1 || echo "FAIL $p"
done
