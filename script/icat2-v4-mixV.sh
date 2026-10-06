#!/usr/bin/env bash
# For the SECOND PC (Codex), 10-06: inheritance mix (mixV) — iCAT-v4 then CAT-47, smoke first. Pre-registered in EXPERIMENT_LOG.md
# ("상속형 혼합(mixV) — 사전 등록 2026-10-06"). mixV = mixT's 9-phase order without the permanent 6 GiB FIO file: at every switch
# the outgoing workload's files are deleted (nodiscard) and the next workload allocates on the freed LBAs (inherits them).
# This PC runs the same pair in the opposite order (CAT-47 then v4), so each PC has its own v4-vs-CAT-47 comparison.
# Usage: bash script/icat2-v4-mixV.sh   (results under result/inherit-20261006/, push to icat-2 as usual)
set -euo pipefail
cd ~/iCAT
K=/lib/modules/$(uname -r)/build
make -C "$K" M="$PWD/online-v4-src" clean >/dev/null 2>&1 || true
make -C "$K" M="$PWD/online-v4-src" -j"$(nproc)" NVMEVIRT_GC_POLICY=WATGC_V2 modules > buildoutput/build-online-v4-icat2.log 2>&1
install -m0644 online-v4-src/nvmev.ko buildoutput/nvmev-online-v4.ko
sha256sum buildoutput/nvmev-online-v4.ko buildoutput/nvmev-varmail-20260908-fixed47.ko
R=result/inherit-20261006
ok() { [[ $(cat $R/$1/exit-code.txt 2>/dev/null) == 0 && $(grep -c '^phase[A-I](' $R/$1/summary.txt 2>/dev/null) -ge 9 ]] && ls $R/$1/extents-*.txt >/dev/null; }
for p in onlinev4 fixed47; do
  env SMOKE=1 PH_SECS=120 bash script/mix-inherit-20261006.sh mixV $p 1
  ok mixV-$p-rep1-smoke || { echo "mixV $p smoke failed"; exit 1; }
  env PH_SECS=4000 bash script/mix-inherit-20261006.sh mixV $p 1
done
