#!/usr/bin/env bash
# For the SECOND PC (Codex), 10-08: screening of two never-swept Filebench workloads (webproxy, fileserver), 30 min each, after the
# Table-3 prep, with CAT-47 (optimal) and CAT-37 (default). Pre-registered in EXPERIMENT_LOG.md ("후보 워크로드 선별 — 2026-10-08").
# A workload whose WAF stays near 1 is cut. Usage: bash script/icat2-screen.sh   (results: result/screen-20261008/, push to icat-2)
set -euo pipefail
cd ~/iCAT
for w in scrWP scrFS; do for p in fixed47 fixed37; do
  env PH_SECS=1800 bash script/screen-20261008.sh $w $p 1 || echo "FAIL $w $p"
done; done
