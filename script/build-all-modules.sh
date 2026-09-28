#!/usr/bin/env bash
# Rebuild every NVMeVirt module used in the experiments for the running kernel.
# Usage: bash script/build-all-modules.sh     (needs linux-headers-$(uname -r); ~15 min)
set -Eeuo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."
K=/lib/modules/$(uname -r)/build; mkdir -p buildoutput; man=buildoutput/build-manifest-$(uname -r).tsv; : > "$man"
b() { # b <tag> <src dir> <make vars...>
    local tag=$1 src=$2; shift 2
    make -C "$K" M="$PWD/$src" clean >/dev/null 2>&1
    make -C "$K" M="$PWD/$src" -j"$(nproc)" "$@" modules > "buildoutput/build-$tag.log" 2>&1 || { echo "BUILD FAIL $tag (buildoutput/build-$tag.log)"; return 1; }
    install -m0644 "$src/nvmev.ko" "buildoutput/nvmev-$tag.ko"
    printf '%s\t%s\t%s\t%s\n' "$tag" "$src" "$*" "$(sha256sum < "buildoutput/nvmev-$tag.ko" | cut -c1-64)" >> "$man"; echo "built $tag"
}
# fixed CAT grid (arm = ki*15 + si*3 + ri) and the named fixed arms
for a in $(seq 0 59); do b "$(printf 'arm%02d' "$a")" varmail-compare-src NVMEVIRT_GC_POLICY=CAT_FIG7 FIXED_ARM="$a"; done
for a in 10 37 47 50; do cp "buildoutput/nvmev-arm$a.ko" "buildoutput/nvmev-fixed$a.ko"; done
b greedy-m            varmail-compare-src NVMEVIRT_GC_POLICY=GREEDY
b online-mix-20260907 online-mix-src      NVMEVIRT_GC_POLICY=WATGC_V2   # iCAT v1
b online-v2           online-v2-src       NVMEVIRT_GC_POLICY=WATGC_V2
b online-v3           online-v3-src       NVMEVIRT_GC_POLICY=WATGC_V2
b online-v4           online-v4-src       NVMEVIRT_GC_POLICY=WATGC_V2
b gh-greedy           gh-src-7236149      NVMEVIRT_GC_POLICY=GREEDY     # original-author scripts
b gh-online           gh-src-7236149      NVMEVIRT_GC_POLICY=WATGC_V2
echo "manifest: $man"
