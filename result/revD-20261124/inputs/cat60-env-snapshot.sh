# Shared paths. Override any of these in the environment.
ICAT_ROOT="${ICAT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
[[ -v SRC_DIR ]] || SRC_DIR="${ICAT_ROOT}/nvmevirt_test"
[[ -v BUILD_DIR ]] || BUILD_DIR="${ICAT_ROOT}/buildoutput"
[[ -v RESULT_DIR ]] || RESULT_DIR="${ICAT_ROOT}/result"
[[ -v WORKLOAD_DIR ]] || WORKLOAD_DIR="${ICAT_ROOT}/workloads"
MNT_DIR="${MNT_DIR:-${ICAT_ROOT}/mnt}"
# The NVMeVirt namespace, identified by its model string (CSL_Virt_MN_01, set in
# admin.c) rather than a fixed index: with no physical NVMe it is nvme0n1.
assert_virtual_dev() {
    local dev name ctrl model serial vendor address
    dev="$(readlink -f "${1:?device required}")" || return 1
    [[ "$dev" =~ ^/dev/(nvme[0-9]+)n1$ && "$dev" != /dev/nvme0n1 && -b "$dev" ]] || return 1
    name="${BASH_REMATCH[1]}"
    ctrl="/sys/class/nvme/$name"
    model="$(cat "$ctrl/model")" || return 1
    [[ "$model" =~ ^CSL_Virt_MN_[0-9]+[[:space:]]*$ ]] || return 1
    [[ -d /sys/module/nvmev ]] || return 1
    serial="$(cat "$ctrl/serial")" || return 1
    vendor="$(cat "$ctrl/device/vendor")" || return 1
    address="$(cat "$ctrl/address")" || return 1
    [[ "$serial" =~ ^CSL_Virt_SN_[0-9]+[[:space:]]*$ && "$vendor" == 0x0c51 && "$address" =~ ^[[:xdigit:]]{4}:10:00\.0$ ]] || return 1
}
detect_dev() {
    local ctrl candidate found=""
    if [[ -n "${DEV:-}" ]]; then
        assert_virtual_dev "$DEV" || { echo "Unsafe DEV override rejected: $DEV" >&2; return 1; }
        readlink -f "$DEV"; return
    fi
    for ctrl in /sys/class/nvme/nvme*; do
        candidate="/dev/$(basename "$ctrl")n1"
        assert_virtual_dev "$candidate" || continue
        [[ -z "$found" ]] || { echo "Multiple virtual devices; refusing selection" >&2; return 1; }
        found="$candidate"
    done
    [[ -n "$found" ]] || return 1
    printf '%s\n' "$found"
}
assert_virtual_mount() {
    local dev="$1" source
    assert_virtual_dev "$dev" || return 1
    source="$(findmnt -rn -M "$MNT_DIR" -o SOURCE)" || return 1
    [[ "$(readlink -f "$source")" == "$(readlink -f "$dev")" ]]
}
KDIR="/lib/modules/$(uname -r)/build"
MEMMAP_START="${MEMMAP_START:-4G}"
MEMMAP_SIZE="${MEMMAP_SIZE:-8192M}"
NVMEV_CPUS="${NVMEV_CPUS:-1,2}"
