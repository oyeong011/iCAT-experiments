#!/usr/bin/env bash
# Usage: run.sh <tag> <workload-basename> [repeat-index]
#   run.sh cat-a100-r7 test3 1
# Env: FIO_RUNTIME (default 1800), FIO_TEST_SIZE (default 6G)
set -Eeuo pipefail
source "$(dirname "$(readlink -f "$0")")/env.sh"
tag="${1:?Usage: run.sh <tag> <workload> [rep]}"
workload="${2:?Usage: run.sh <tag> <workload> [rep]}"
rep="${3:-1}"
export FIO_TARGET="${MNT_DIR}/test.dat"
export FIO_TEST_SIZE="${FIO_TEST_SIZE:-6G}"
export FIO_RUNTIME="${FIO_RUNTIME:-1800}"
export FIO_IO_SIZE="${FIO_IO_SIZE:-200G}"
export FIO_PHASE_RUNTIME="${FIO_PHASE_RUNTIME:-600}"

run_id="$(date '+%Y%m%d-%H%M%S')-$$"
mkdir -p "${RESULT_DIR}"
log="${RESULT_DIR}/${workload}-${tag}-rep${rep}-${run_id}.log"
start_marker="iCAT_START tag=${tag} workload=${workload} rep=${rep} run=${run_id}"
end_marker="iCAT_END tag=${tag} workload=${workload} rep=${rep} run=${run_id}"

started=0
sudo_keepalive=""
finish() {
	local rc=$?
	trap - EXIT
	kill "${sudo_keepalive}" 2>/dev/null || true
	if ((started)); then "${ICAT_ROOT}/script/end_virt.sh" || true; fi
	echo "${end_marker}" | sudo tee /dev/kmsg >/dev/null
	sudo dmesg --color=never | awk -v s="${start_marker}" -v e="${end_marker}" '
		index($0,s){c=1;next} index($0,e){c=0;next} c{print}' > "${log}"
	echo "[RESULT] ${log}"
	exit "${rc}"
}

# A run outlasts the default 15-minute sudo timestamp, and the teardown at the
# end needs sudo again; keep it warm so the sweep stays unattended.
if ! sudo -n true 2>/dev/null; then
	sudo -v
	while true; do sudo -n true; sleep 60; kill -0 "$$" 2>/dev/null || exit; done &
	sudo_keepalive=$!
fi
trap finish EXIT
echo "${start_marker}" | sudo tee /dev/kmsg >/dev/null
"${ICAT_ROOT}/script/start_virt.sh" "${tag}"
started=1
fio "${WORKLOAD_DIR}/preset.fio"
fio "${WORKLOAD_DIR}/${workload}.fio"
