#!/usr/bin/env bash
# Usage: start_virt.sh <tag>   -- loads buildoutput/nvmev-<tag>.ko and mounts a fresh ext4
set -Eeuo pipefail
source "$(dirname "$(readlink -f "$0")")/env.sh"
tag="${1:?Usage: start_virt.sh <tag>}"
module="${BUILD_DIR}/nvmev-${tag}.ko"
[[ -f "${module}" ]] || { echo "missing module: ${module}" >&2; exit 2; }
if grep -q '^nvmev ' /proc/modules; then
	sudo umount "${MNT_DIR}" 2>/dev/null || true
	sudo rmmod nvmev
	sleep 1
fi
mkdir -p "${MNT_DIR}"
sudo insmod "${module}" memmap_start="${MEMMAP_START}" memmap_size="${MEMMAP_SIZE}" cpus="${NVMEV_CPUS}"
trap 'sudo rmmod nvmev 2>/dev/null || true' ERR

dev=""
for _ in $(seq 1 50); do
	if dev="$(detect_dev)" && [[ -b "${dev}" ]]; then break; fi
	sleep 0.2
done
[[ -b "${dev:-}" ]] || { echo "NVMeVirt namespace never appeared" >&2; exit 2; }
echo "[DEV] ${dev}"

echo y | sudo mkfs.ext4 "${dev}" >/dev/null
sudo mount -o nodiscard "${dev}" "${MNT_DIR}"
sudo chown -R "$(id -un):$(id -gn)" "${MNT_DIR}"
echo "Virt ready: ${MNT_DIR}"
