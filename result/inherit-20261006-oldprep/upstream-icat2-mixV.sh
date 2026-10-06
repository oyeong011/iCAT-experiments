#!/usr/bin/env bash
# For the SECOND PC (Codex), 10-06: inheritance mix (mixV) — CAT-37 (default) then CAT-50 (robust), smoke first.
# Pre-registered in EXPERIMENT_LOG.md ("상속형 혼합(mixV)"). This PC runs CAT-47 (optimal) then iCAT-v4.
# mixV = mixT's 9-phase order without a 6 GiB FIO file kept from the start; each switch keeps or deletes data like the
# matching Table-3 two-phase mix. Modules are the committed buildoutput/nvmev-fixed37.ko / nvmev-fixed50.ko (same as mixT 10-04).
# Usage: bash script/icat2-mixV.sh   (results under result/inherit-20261006/, push to icat-2 as usual)
set -euo pipefail
cd ~/iCAT
sha256sum buildoutput/nvmev-fixed37.ko buildoutput/nvmev-fixed50.ko
R=result/inherit-20261006
ok() { [[ $(cat $R/$1/exit-code.txt 2>/dev/null) == 0 && $(grep -c '^phase[A-I](' $R/$1/summary.txt 2>/dev/null) -ge 9 ]] && ls $R/$1/extents-*.txt >/dev/null; }
for p in fixed37 fixed50; do
  env SMOKE=1 PH_SECS=120 bash script/mix-inherit-20261006.sh mixV $p 1
  ok mixV-$p-rep1-smoke || { echo "mixV $p smoke failed"; exit 1; }
  env PH_SECS=4000 bash script/mix-inherit-20261006.sh mixV $p 1
done
