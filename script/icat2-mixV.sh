#!/usr/bin/env bash
# For the SECOND PC (Codex), 10-06: inheritance mix (mixV) — CAT-37 (default) then CAT-50 (robust), smoke first.
# Pre-registered in EXPERIMENT_LOG.md ("상속형 혼합(mixV)"). This PC runs CAT-47 (optimal) then iCAT-v4.
# mixV = mixT's 9-phase order without a 6 GiB FIO file kept from the start; each switch keeps or deletes data like the
# matching Table-3 two-phase mix; prep identical to Table 3 (6 GiB FIO file kept all run, revised 10-06 13:00). Modules are the committed buildoutput/nvmev-fixed37.ko / nvmev-fixed50.ko (same as mixT 10-04).
# Usage: bash script/icat2-mixV.sh   (results under result/inherit-20261006/, push to icat-2 as usual)
set -euo pipefail
cd ~/iCAT
sha256sum buildoutput/nvmev-fixed37.ko buildoutput/nvmev-fixed50.ko
R=result/inherit-20261006
ok() { [[ $(cat $R/$1/exit-code.txt 2>/dev/null) == 0 && $(grep -c '^phase[A-I](' $R/$1/summary.txt 2>/dev/null) -ge 9 ]] && ! grep -qi 'no space left' $R/$1/*.txt; }
for p in fixed37 fixed50; do
  # full-size short check (DB 600k, 60 s per phase): catches ENOSPC that SMOKE=1's tiny DB cannot
  env PH_SECS=60 MIX_BASE=$PWD/$R/fitcheck bash script/mix-inherit-20261006.sh mixV $p 1
  R0=$R; R=$R/fitcheck; ok mixV-$p-rep1 || { echo "mixV $p full-size short check failed"; exit 1; }; R=$R0
  env PH_SECS=4000 bash script/mix-inherit-20261006.sh mixV $p 1
done
