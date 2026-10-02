#!/usr/bin/env bash
set -Eeuo pipefail
root=/home/oy/iCAT
batch="$root/result/cat-sweep-20260906"
journal="$root/EXPERIMENT_LOG.md"
export ICAT_ROOT="$root" FIO_RUNTIME=600 FIO_TEST_SIZE=6G
export MEMMAP_START=4G MEMMAP_SIZE=8192M NVMEV_CPUS=1,2 MNT_DIR="$root/mnt"
unset DEV
scales=(25 50 100 200 400)
ratios=(4 7 16)
mode=${1:?Use plan, build, or run}
mkdir -p "$batch"
if [[ "$mode" == plan ]]; then
    n=0
    for rep in 1 2 3; do
        for step in {0..14}; do
            index=$(((step * 7 + (rep - 1) * 5) % 15))
            scale=${scales[$((index / 3))]}
            ratio=${ratios[$((index % 3))]}
            for workload in test2 test3; do
                [[ "$workload:$scale:$ratio" == test3:100:7 ]] && continue
                n=$((n + 1))
                printf '%03d\t%s\t%s\t%s\t%s\n' "$n" "$workload" "$scale" "$ratio" "$rep"
            done
        done
    done
    exit
fi
exec 9>"$batch/batch.lock"
flock -n 9 || exit 1
if [[ "$mode" == build ]]; then
    for scale in "${scales[@]}"; do
        for ratio in "${ratios[@]}"; do
            tag="sweep-20260906-a$scale-r$ratio"
            bash "$root/script/build.sh" "$tag" NVMEVIRT_GC_POLICY=CAT_FIG7 \
                NVMEVIRT_AGE_MODE=CREATE NVMEVIRT_CAT_SCALE_PCT="$scale" \
                NVMEVIRT_CAT_AGE_RATIO="$ratio" NVMEVIRT_WAF_WINDOW_PAGES=262144 \
                > "$batch/build-a$scale-r$ratio.txt" 2>&1
            echo "Built $tag"
        done
    done
    cmp "$root/buildoutput/nvmev-sweep-20260906-a100-r7.ko" \
        "$root/buildoutput/nvmev-baseline-20260906-cat.ko"
    sha256sum "$root"/buildoutput/nvmev-sweep-20260906-*.ko > "$batch/modules.sha256"
    exit
fi
[[ "$mode" == run ]] || exit 2
current=preflight
finish() {
    rc=$?
    printf '\n- cat-sweep batch exit=%s at %s; last stage=%s\n' "$rc" "$(date -Is)" "$current" >> "$journal"
}
trap finish EXIT
while IFS=$'\t' read -r id workload scale ratio rep; do
    current="run-$id"
    tag="sweep-20260906-a$scale-r$ratio"
    prefix="$batch/run-$id"
    [[ ! -e "$prefix.console.txt" && ! -e "$prefix.environment.txt" ]] || exit 1
    printf '\n### cat-sweep-20260906 run-%s — started %s\n\n- Workload=%s scale=%s ratio=%s repetition=%s, runtime=600\n- Command: `script/run.sh %s %s %s`\n- Environment: [snapshot](result/cat-sweep-20260906/run-%s.environment.txt)\n- Console: [output](result/cat-sweep-20260906/run-%s.console.txt)\n' \
        "$id" "$(date -Is)" "$workload" "$scale" "$ratio" "$rep" "$tag" "$workload" "$rep" "$id" "$id" >> "$journal"
    [[ ! -e /sys/module/nvmev ]] && ! mountpoint -q "$MNT_DIR" || exit 1
    if compgen -G '/sys/class/nvme/nvme*' >/dev/null; then exit 1; fi
    sha256sum --check --status "$batch/inputs.sha256"
    sha256sum --check --status "$batch/modules.sha256"
    {
        date -Is
        uname -a
        cat /proc/cmdline
        fio --version
        sha256sum "$root/buildoutput/nvmev-$tag.ko"
        cat "$root/buildoutput/nvmev-$tag.build-info.txt"
        sha256sum "$root/workloads/$workload.fio" "$root/workloads/preset.fio"
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
        printf 'runtime=600 preset=6G memmap_start=4G memmap_size=8192M cpus=1,2 mount=%s\n' "$MNT_DIR"
    } > "$prefix.environment.txt"
    echo "Starting $id/087: $workload scale=$scale ratio=$ratio rep=$rep"
    set +e
    bash "$root/script/run.sh" "$tag" "$workload" "$rep" > "$prefix.console.txt" 2>&1
    rc=$?
    set -e
    log=$(awk '/^\[RESULT\] / {print $2}' "$prefix.console.txt" | tail -1)
    printf '\n- Finished: %s; run exit=%s\n' "$(date -Is)" "$rc" >> "$journal"
    [[ "$rc" == 0 && -f "$log" ]] || exit 1
    printf -- '- Kernel log: [%s](result/%s)\n' "$(basename "$log")" "$(basename "$log")" >> "$journal"
    awk '/GC stats:/ {print "- Raw counters: `" $0 "`"}' "$log" >> "$journal"
    grep -q "GC stats: policy=cat-fig7 age_mode=create .*scale_pct=$scale age_ratio=$ratio$" "$log"
    [[ ! -e /sys/module/nvmev ]] && ! mountpoint -q "$MNT_DIR" || exit 1
    echo '- Cleanup: module absent and target unmounted.' >> "$journal"
    echo "Finished $id/087"
done < "$batch/plan.tsv"
current=complete
echo '- All 87 new runs completed; analysis pending.' >> "$journal"
