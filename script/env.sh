# Shared paths. Override any of these in the environment.
ICAT_ROOT="${ICAT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SRC_DIR="${ICAT_ROOT}/nvmevirt_test"
BUILD_DIR="${ICAT_ROOT}/buildoutput"
RESULT_DIR="${ICAT_ROOT}/result"
WORKLOAD_DIR="${ICAT_ROOT}/workloads"
MNT_DIR="${MNT_DIR:-${ICAT_ROOT}/mnt}"
# The NVMeVirt namespace, identified by its model string (CSL_Virt_MN_01, set in
# admin.c) rather than a fixed index: with no physical NVMe it is nvme0n1.
detect_dev() {
	local ctrl
	if [[ -n "${DEV:-}" ]]; then printf '%s\n' "${DEV}"; return; fi
	for ctrl in /sys/class/nvme/nvme*; do
		[[ -r "${ctrl}/model" ]] || continue
		if grep -qiE "CSL_Virt|nvmevirt" "${ctrl}/model"; then
			printf '/dev/%sn1\n' "$(basename "${ctrl}")"
			return
		fi
	done
	return 1
}
KDIR="/lib/modules/$(uname -r)/build"
MEMMAP_START="${MEMMAP_START:-4G}"
MEMMAP_SIZE="${MEMMAP_SIZE:-8192M}"
NVMEV_CPUS="${NVMEV_CPUS:-1,2}"
