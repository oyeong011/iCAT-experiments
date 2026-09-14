#!/usr/bin/env bash
set -Eeuo pipefail
root=/home/oy/iCAT
batch="$root/result/measured-cat-20260907"
journal="$root/EXPERIMENT_LOG.md"
control=/proc/nvmevirt_measurement
export FIO_TARGET="$root/mnt/test.dat"
mode=${1:?Use plan, build, batch, or one}
mkdir -p "$batch"
if [[ "$mode" == plan ]]; then
    scales=(100 400 200)
    ratios=(7 16 7)
    n=0
    for rep in 1 2 3; do
        for step in 0 1 2; do
            index=$(((step + rep - 1) % 3))
            for workload in test2 test3; do
                n=$((n+1))
                printf '%02d\t%s\t%s\t%s\t%s\n' "$n" "$workload" "${scales[$index]}" "${ratios[$index]}" "$rep"
            done
        done
    done
    exit
fi
if [[ "$mode" == build ]]; then
    for pair in 100:7 400:16 200:7; do
        scale=${pair%:*}; ratio=${pair#*:}
        tag="measured-20260907-a$scale-r$ratio"
        bash "$root/script/build.sh" "$tag" NVMEVIRT_GC_POLICY=CAT_FIG7 \
            NVMEVIRT_AGE_MODE=CREATE NVMEVIRT_CAT_SCALE_PCT="$scale" NVMEVIRT_CAT_AGE_RATIO="$ratio" \
            NVMEVIRT_WAF_WINDOW_PAGES=262144 > "$batch/build-a$scale-r$ratio.txt" 2>&1
        echo "Built $tag"
    done
    cmp "$root/buildoutput/nvmev-measured-20260907-a100-r7.ko" "$root/buildoutput/nvmev-measurement-20260907-cat-v2.ko"
    sha256sum "$root"/buildoutput/nvmev-measured-20260907-*.ko > "$batch/modules.sha256"
    exit
fi
if [[ "$mode" == batch ]]; then
    exec 9>"$batch/batch.lock"
    flock -n 9 || exit 1
    trap 'printf "\n- measured-cat batch exit=%s at %s\n" "$?" "$(date -Is)" >> "$journal"' EXIT
    while IFS=$'\t' read -r id workload scale ratio rep; do
        echo "Starting $id/18 $workload $scale/$ratio seed-round=$rep"
        [[ ! -e "$batch/run-$id.console.txt" ]] || exit 1
        bash "$0" one "$id" "$workload" "$scale" "$ratio" "$rep" > "$batch/run-$id.console.txt" 2>&1
        echo "Finished $id/18"
    done < "$batch/plan.tsv"
    echo '- measured-cat: all 18 runs complete; analysis pending.' >> "$journal"
    exit
fi
[[ "$mode" == one && "$#" == 6 ]] || exit 2
id=$2; workload=$3; scale=$4; ratio=$5; rep=$6
dir="$batch/run-$id"
[[ ! -e "$dir" ]] || exit 1
mkdir -p "$dir"
tag="measured-20260907-a$scale-r$ratio"
export SEED_HOT=$((20260910+rep)) SEED_WARM=$((20261010+rep)) SEED_COLD=$((20261110+rep))
printf '\n### measured-cat-20260907 run-%s — started %s\n\n- %s scale=%s ratio=%s, seed hot/warm/cold=%s/%s/%s, measured payload=24576000000 bytes.\n- Evidence: `result/measured-cat-20260907/run-%s/`, console `run-%s.console.txt`.\n' \
    "$id" "$(date -Is)" "$workload" "$scale" "$ratio" "$SEED_HOT" "$SEED_WARM" "$SEED_COLD" "$id" "$id" >> "$journal"
loaded=0
marker="measured-cat-$id-$$"
finish() {
    rc=$?
    trap - EXIT
    if ((loaded)); then
        if [[ -w "$control" ]]; then cat "$control" > "$dir/final-control.txt"; fi
        if mountpoint -q "$root/mnt"; then sudo -n umount "$root/mnt" || rc=1; fi
        sudo -n rmmod nvmev || rc=1
    fi
    sudo -n dmesg --color=never | awk -v s="$marker" 'index($0,s){on=1}on' > "$dir/kernel.log"
    printf '\n- Finished %s; run exit=%s\n' "$(date -Is)" "$rc" >> "$journal"
    if [[ -f "$dir/summary.txt" ]]; then sed 's/^/- /' "$dir/summary.txt" >> "$journal"; fi
    echo "RUN $id exit=$rc"
    exit "$rc"
}
trap finish EXIT
trap 'printf "FAIL line=%s command=%s\n" "$LINENO" "$BASH_COMMAND" >&2' ERR
[[ ! -e /sys/module/nvmev ]] && ! mountpoint -q "$root/mnt"
if compgen -G '/sys/class/nvme/nvme*' >/dev/null; then exit 1; fi
sha256sum --check --status "$batch/inputs.sha256"
sha256sum --check --status "$batch/modules.sha256"
{
    date -Is; uname -a; cat /proc/cmdline; fio --version
    cat "$root/buildoutput/nvmev-$tag.build-info.txt"
    sha256sum "$root/buildoutput/nvmev-$tag.ko"
    lscpu; free -h; uptime
    for cpu in 1 2; do
        for field in scaling_governor scaling_cur_freq; do
            file="/sys/devices/system/cpu/cpu$cpu/cpufreq/$field"
            printf '%s=' "$file"; if [[ -r "$file" ]]; then cat "$file"; else echo unavailable; fi
        done
    done
} > "$dir/environment.txt"
printf '%s\n' "$marker" | sudo -n tee /dev/kmsg >/dev/null
sudo -n insmod "$root/buildoutput/nvmev-$tag.ko" memmap_start=4G memmap_size=8192M cpus=1,2 measurement_manual=1 measurement_uid="$(id -u)"
loaded=1
for attempt in {1..50}; do
    [[ -b /dev/nvme0n1 && -w "$control" ]] && break
    sleep 0.2
done
[[ -b /dev/nvme0n1 && -w "$control" ]]
grep -q CSL_Virt /sys/class/nvme/nvme0/model
sudo -n mkfs.ext4 /dev/nvme0n1 > "$dir/mkfs.txt" 2>&1
sudo -n mount -o nodiscard /dev/nvme0n1 "$root/mnt"
sudo -n chown -R oy:oy "$root/mnt"
fio --name=preset --filename="$FIO_TARGET" --size=6G --rw=write --bs=128k --direct=1 --ioengine=libaio --iodepth=32 --end_fsync=1 --output-format=json --output="$dir/preset.json"
fio --name=prepare --filename="$FIO_TARGET" --size=6G --io_size=3G --rw=randwrite --bs=4k --direct=1 --ioengine=libaio --iodepth=32 --rate_iops=10000 --randrepeat=1 --randseed=20260907 --end_fsync=1 --output-format=json --output="$dir/prepare.json"
sync -f "$FIO_TARGET"
jq -s -e 'all(.[]; all(.jobs[]; .error == 0))' "$dir/preset.json" "$dir/prepare.json" >/dev/null
cat "$control" > "$dir/prepared.txt"
field() { awk -v key="$2" 'NR==1{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]==key)print a[2]}}' "$1"; }
sectors() { awk '{print $7}' /sys/class/block/nvme0n1/stat; }
[[ $(field "$dir/prepared.txt" host_bytes) == 0 && $(field "$dir/prepared.txt" gc_pages) == 0 ]]
before=$(sectors)
printf 'start\n' > "$control"
[[ "$before" == "$(sectors)" ]]
cat "$control" > "$dir/started.txt"
[[ $(field "$dir/started.txt" host_bytes) == 0 ]]
echo "Measured phase started $(date -Is)"
fio "$root/workloads/measured-$workload.fio" --output-format=json --output="$dir/measured.json"
sync -f "$FIO_TARGET"
stop_before=$(sectors)
printf 'stop\n' > "$control"
after=$(sectors)
[[ "$stop_before" == "$after" ]]
cat "$control" > "$dir/stopped.txt"
jq -e 'all(.jobs[]; .error == 0) and ([.jobs[].write.io_bytes] | add == 24576000000)' "$dir/measured.json" >/dev/null
host=$(field "$dir/stopped.txt" host_pages)
gc=$(field "$dir/stopped.txt" gc_pages)
bytes=$(field "$dir/stopped.txt" host_bytes)
[[ "$bytes" == "$(((after-before)*512))" && "$bytes" == "$((host*4096))" ]]
[[ "$bytes" -ge 24576000000 && $(field "$dir/stopped.txt" active) == 0 ]]
awk -v h="$host" -v g="$gc" -v b="$bytes" 'BEGIN{printf "host_bytes=%.0f payload_bytes=24576000000 extra_host_bytes=%.0f host_pages=%.0f gc_pages=%.0f WAF=%.9f\n",b,b-24576000000,h,g,1+g/h}' > "$dir/summary.txt"
