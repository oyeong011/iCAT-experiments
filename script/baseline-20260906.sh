#!/usr/bin/env bash
set -Eeuo pipefail
root=/home/oy/iCAT
batch="$root/result/baseline-20260906"
journal="$root/EXPERIMENT_LOG.md"
mkdir -p "$batch"
exec 9>"$batch/batch.lock"
flock -n 9 || exit 1
export ICAT_ROOT="$root" FIO_RUNTIME=600 FIO_TEST_SIZE=6G
export MEMMAP_START=4G MEMMAP_SIZE=8192M NVMEV_CPUS=1,2
export MNT_DIR="$root/mnt"
unset DEV
sequence=(greedy cat cat greedy greedy cat)
for index in "${!sequence[@]}"; do
    number=$((index + 1))
    policy="${sequence[$index]}"
    tag="baseline-20260906-$policy"
    prefix="$batch/run-$number-$policy"
    [[ ! -e "$prefix.console.txt" ]] || { echo "Existing run: $prefix"; exit 1; }
    if [[ -e /sys/module/nvmev ]] || mountpoint -q "$MNT_DIR"; then
        echo "Device already active; stopping before run $number"
        exit 1
    fi
    if compgen -G '/sys/class/nvme/nvme*' >/dev/null; then
        echo "Unexpected NVMe controller; stopping before run $number"
        exit 1
    fi
    {
        date -Is
        uname -a
        cat /proc/cmdline
        fio --version
        sha256sum "$root/buildoutput/nvmev-$tag.ko"
        sha256sum "$root/workloads/test3.fio" "$root/workloads/preset.fio"
        cat "$root/buildoutput/nvmev-$tag.build-info.txt"
        lscpu
        free -h
        uptime
        for cpu in 1 2; do
            for field in scaling_governor scaling_cur_freq; do
                file="/sys/devices/system/cpu/cpu$cpu/cpufreq/$field"
                printf '%s=' "$file"
                if [[ -r "$file" ]]; then cat "$file"; else echo unavailable; fi
            done
        done
        ps -eo pid,comm,pcpu,pmem --sort=-pcpu | head -20 || true
        printf 'ICAT_ROOT=%s FIO_RUNTIME=%s FIO_TEST_SIZE=%s MEMMAP_START=%s MEMMAP_SIZE=%s NVMEV_CPUS=%s\n' \
            "$ICAT_ROOT" "$FIO_RUNTIME" "$FIO_TEST_SIZE" "$MEMMAP_START" "$MEMMAP_SIZE" "$NVMEV_CPUS"
    } > "$prefix.environment.txt"
    printf '\n### baseline-20260906 run-%s %s — started %s\n\n- Command: `FIO_RUNTIME=600 script/run.sh %s test3 %s`\n- Environment: [snapshot](result/baseline-20260906/run-%s-%s.environment.txt)\n- Output: [console](result/baseline-20260906/run-%s-%s.console.txt)\n' \
        "$number" "$policy" "$(date -Is)" "$tag" "$number" "$number" "$policy" "$number" "$policy" >> "$journal"
    set +e
    bash "$root/script/run.sh" "$tag" test3 "$number" 2>&1 | tee "$prefix.console.txt"
    rc=${PIPESTATUS[0]}
    set -e
    log=$(awk '/^\[RESULT\] / {print $2}' "$prefix.console.txt" | tail -1)
    {
        printf '\n- Finished: %s; run exit=%s\n' "$(date -Is)" "$rc"
        if [[ -f "$log" ]]; then
            printf -- '- Kernel log: [%s](result/%s)\n' "$(basename "$log")" "$(basename "$log")"
            awk '/GC stats:/ {print "- Raw counters: `" $0 "`"}' "$log"
        else
            echo '- Kernel log missing.'
        fi
        if [[ -e /sys/module/nvmev ]] || mountpoint -q "$MNT_DIR"; then
            echo '- Cleanup: FAILED; batch stopping.'
        else
            echo '- Cleanup: module absent and target unmounted.'
        fi
    } >> "$journal"
    [[ "$rc" == 0 && -f "$log" ]] || exit 1
    [[ ! -e /sys/module/nvmev ]] && ! mountpoint -q "$MNT_DIR" || exit 1
    grep -q 'GC stats:' "$log" || exit 1
done
printf '\n- baseline-20260906: all six executions finished at %s; statistical review pending.\n' "$(date -Is)" >> "$journal"
echo 'BATCH EXECUTION COMPLETE; statistical review pending.'
