#!/usr/bin/env bash
cd /home/oy/iCAT; K=/lib/modules/$(uname -r)/build; mkdir -p result/sweep-20260915
for a in $(seq 0 59); do t=$(printf 'arm%02d' $a)
  make -C $K M=$PWD/varmail-compare-src clean >/dev/null 2>&1
  make -C $K M=$PWD/varmail-compare-src -j8 NVMEVIRT_GC_POLICY=CAT_FIG7 NVMEVIRT_CAT_K=7 NVMEVIRT_CAT_SCALE_PCT=100 NVMEVIRT_CAT_AGE_RATIO=7 FIXED_ARM=$a modules > result/sweep-20260915/build-$t.log 2>&1 && install -m0644 varmail-compare-src/nvmev.ko buildoutput/nvmev-$t.ko || echo "BUILD FAIL $t"
done
sha256sum buildoutput/nvmev-arm*.ko > result/sweep-20260915/modules.sha256
echo BUILDDONE $(ls buildoutput/nvmev-arm*.ko | wc -l)
