#!/usr/bin/env bash
# For the SECOND PC (Codex), 10-05: build iCAT-v6 and run it on the irregular 10 h mix (mixT).
# v6 = v5 + change detection that does not wait for settling: a sample > 25% from the current arm's own mean
# pauses elimination; 3 in a row reset the learner with ALL 45 arms (full re-sweep).
# Usage: bash script/icat2-v6-mixT.sh      (results under result/mix-20260911/, push to icat-2 as usual)
set -euo pipefail
cd ~/iCAT
K=/lib/modules/$(uname -r)/build
make -C "$K" M="$PWD/online-v6-src" clean >/dev/null 2>&1 || true
make -C "$K" M="$PWD/online-v6-src" -j"$(nproc)" NVMEVIRT_GC_POLICY=WATGC_V2 modules > buildoutput/build-online-v6.log 2>&1
install -m0644 online-v6-src/nvmev.ko buildoutput/nvmev-online-v6.ko
sha256sum buildoutput/nvmev-online-v6.ko
env SMOKE=1 PH_SECS=120 bash script/mix-20260911.sh mixT onlinev6 1
[[ $(grep -c '^phase' result/mix-20260911/mixT-onlinev6-rep1-smoke/summary.txt) -ge 9 ]] || { echo "v6 smoke failed"; exit 1; }
env PH_SECS=4000 bash script/mix-20260911.sh mixT onlinev6 1
