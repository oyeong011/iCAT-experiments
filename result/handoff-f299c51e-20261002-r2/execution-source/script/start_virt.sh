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
grep -Fq 'memmap=8G$4G' /proc/cmdline || { echo "Missing reserved memory" >&2; exit 2; }
[[ "$MEMMAP_START" == 4G && "$MEMMAP_SIZE" == 8192M ]] || exit 2
mountpoint -q "$MNT_DIR" && { echo "Mount point already occupied" >&2; exit 2; }
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

assert_virtual_dev "$dev" || { echo "Unsafe device" >&2; exit 2; }
[[ -z "$(lsblk -nr -o MOUNTPOINTS "$dev" | tr -d '[:space:]')" ]] || exit 2
cat "/sys/class/nvme/$(basename "$dev" n1)/model"
echo y | sudo mkfs.ext4 "${dev}" >/dev/null
sudo mount -o nodiscard "${dev}" "${MNT_DIR}"
sudo chown -R "$(id -un):$(id -gn)" "${MNT_DIR}"
assert_virtual_mount "$dev" || exit 2
echo "Virt ready: ${MNT_DIR}"
