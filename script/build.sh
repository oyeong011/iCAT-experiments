#!/usr/bin/env bash
# Usage: build.sh <tag> [MAKE_VAR=VALUE ...]
#   build.sh greedy               NVMEVIRT_GC_POLICY=GREEDY
#   build.sh cat-a100-r7          NVMEVIRT_GC_POLICY=CAT_FIG7 NVMEVIRT_CAT_SCALE_PCT=100
set -Eeuo pipefail
source "$(dirname "$(readlink -f "$0")")/env.sh"
tag="${1:?Usage: build.sh <tag> [MAKE_VAR=VALUE ...]}"; shift
mkdir -p "${BUILD_DIR}"
make -C "${KDIR}" M="${SRC_DIR}" clean >/dev/null
make -C "${KDIR}" M="${SRC_DIR}" -j"$(nproc)" modules "$@"
install -m 0644 "${SRC_DIR}/nvmev.ko" "${BUILD_DIR}/nvmev-${tag}.ko"
printf 'tag=%s\nmake_vars=%s\nbuilt_at=%s\nsha256=%s\n' \
	"${tag}" "$*" "$(date -Is)" "$(sha256sum "${BUILD_DIR}/nvmev-${tag}.ko" | cut -d' ' -f1)" \
	> "${BUILD_DIR}/nvmev-${tag}.build-info.txt"
echo "[OUTPUT] ${BUILD_DIR}/nvmev-${tag}.ko"
