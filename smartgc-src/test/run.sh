#!/usr/bin/env bash
# Build the userspace FTL driver (test/sim.c) for one GC policy and run it.
# Usage: bash smartgc-src/test/run.sh <smartgc|greedy|arm00..arm59> [sim options, see sim.c]
# SIM_SRC=<dir> builds another copy of the module source (e.g. varmail-compare-src) with the same driver.
# The binary and the generated <linux/...> stubs go to $SIM_OUT (default: a temp dir), not into the source tree.
set -Eeuo pipefail
here=$(dirname "$(readlink -f "$0")")
src=$(readlink -f "${SIM_SRC:-$here/..}")
policy=${1:?Use smartgc, greedy or armNN}; shift
case "$policy" in
    smartgc) flags="-DCONV_GC_POLICY=3";;
    greedy) flags="-DCONV_GC_POLICY=0";;
    arm[0-5][0-9]) flags="-DCONV_GC_POLICY=1 -DCONV_FIXED_ARM=$((10#${policy#arm}))";;
    *) echo "unknown policy $policy" >&2; exit 2;;
esac
out=${SIM_OUT:-$(mktemp -d)}
mkdir -p "$out/shim/linux/sched" "$out/shim/asm"
for h in types vmalloc slab ktime math64 sched/clock time64 string module mutex proc_fs uaccess user_namespace kthread highmem; do
    echo '#include "kshim.h"' > "$out/shim/linux/$h.h"
done
# shellcheck disable=SC2086
gcc -O2 -g -std=gnu17 -Wall -Wno-unused-variable -Wno-unused-function -Wno-unused-but-set-variable -Wno-format \
    -DBASE_SSD=SAMSUNG_970PRO $flags -I"$out/shim" -I"$here" -I"$src" \
    -o "$out/sim-$policy" "$here/sim.c"
"$out/sim-$policy" "$@"
