#!/usr/bin/env bash
# Usage: matrix.sh a|b [reps]
#   a  age-definition decision: greedy vs CAT(create) vs CAT(last-inval)
#   b  alpha / age-ratio ablation on AGE_MODE (default CREATE; override with AGE_MODE=LAST_INVAL)
# Env: FIO_RUNTIME (default 1800), WORKLOADS (default "test2 test3")
set -Eeuo pipefail
source "$(dirname "$(readlink -f "$0")")/env.sh"
stage="${1:?Usage: matrix.sh a|b [reps]}"
reps="${2:-3}"
workloads="${WORKLOADS:-test2 test3}"
age_mode="${AGE_MODE:-CREATE}"
cd "${ICAT_ROOT}/script"

declare -a tags
build() { # build <tag> <make vars...>
	./build.sh "$@" >/dev/null
	tags+=("$1")
}

case "${stage}" in
a)
	build greedy NVMEVIRT_GC_POLICY=GREEDY
	build cat-create NVMEVIRT_GC_POLICY=CAT_FIG7 NVMEVIRT_AGE_MODE=CREATE
	build cat-lastinval NVMEVIRT_GC_POLICY=CAT_FIG7 NVMEVIRT_AGE_MODE=LAST_INVAL
	;;
b)
	build greedy NVMEVIRT_GC_POLICY=GREEDY
	for a in 5 10 25 50 100 200 400; do
		build "cat-a${a}-r7" NVMEVIRT_GC_POLICY=CAT_FIG7 \
			NVMEVIRT_AGE_MODE="${age_mode}" NVMEVIRT_CAT_SCALE_PCT="${a}"
	done
	for r in 4 16; do
		build "cat-a100-r${r}" NVMEVIRT_GC_POLICY=CAT_FIG7 \
			NVMEVIRT_AGE_MODE="${age_mode}" NVMEVIRT_CAT_AGE_RATIO="${r}"
	done
	;;
*) echo "unknown stage: ${stage}" >&2; exit 2 ;;
esac

# Randomize the order so that drift in machine state does not track configuration.
for rep in $(seq 1 "${reps}"); do
	for w in ${workloads}; do
		for tag in $(printf '%s\n' "${tags[@]}" | shuf); do
			echo "=== rep=${rep} workload=${w} tag=${tag}"
			./run.sh "${tag}" "${w}" "${rep}" || \
				echo "!!! FAILED rep=${rep} workload=${w} tag=${tag}" >&2
		done
	done
done
