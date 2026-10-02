#!/usr/bin/env bash
set -Eeuo pipefail
root=/home/oy/iCAT
base="$root/result/varmail-20260908"
control=/proc/nvmevirt_measurement
journal="$root/EXPERIMENT_LOG.md"
mode=${1:?Use barrier, smoke, main, or batch}
field() { awk -v key="$2" 'NR==1{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]==key)print a[2]}}' "$1"; }
sectors() { awk '{print $7}' /sys/class/block/nvme0n1/stat; }
if [[ "$mode" == barrier ]]; then
    run=${2:?Run ID required}
    [[ "$run" =~ ^(smoke|main)-(fixed37|fixed47|online)$ ]] || exit 2
    dir="$base/$run"
    trap 'rc=$?; if ((rc)); then printf "%s\n" "$rc" > "$dir/barrier-failed.txt"; while true; do sleep 30; done; fi' EXIT
    [[ -d "$dir" && -w "$control" ]]
    sync -f "$root/mnt"
    cat "$control" > "$dir/prepared.txt"
    [[ $(field "$dir/prepared.txt" host_bytes) == 0 ]]
    df -B1 "$root/mnt" > "$dir/prepared-space.txt"
    before=$(sectors)
    printf 'start\n' > "$control"
    [[ "$before" == "$(sectors)" ]]
    printf '%s\n' "$before" > "$dir/before-sectors.txt"
    cat "$control" > "$dir/started.txt"
    [[ $(field "$dir/started.txt" active) == 1 && $(field "$dir/started.txt" host_bytes) == 0 ]]
    date -Is > "$dir/measurement-start.txt"
    printf 'varmail-%s MEASURE_START\n' "$run" | sudo -n tee /dev/kmsg >/dev/null
    exit
fi
if [[ "$mode" == batch ]]; then
    for policy in fixed47 online fixed37; do
        bash "$0" smoke "$policy" > "$base/smoke-$policy.console.txt" 2>&1
        echo "PASS smoke $policy"
    done
    for policy in fixed47 online fixed37; do
        bash "$0" main "$policy" > "$base/main-$policy.console.txt" 2>&1
        echo "PASS main $policy"
    done
    exit
fi
policy=${2:?Policy required}
case "$mode" in smoke) seconds=60;; main) seconds=3600;; *) exit 2;; esac
case "$policy" in
    fixed37|fixed47) tag="varmail-20260908-$policy";;
    online) tag=online-mix-20260907;;
    *) exit 2;;
esac
run="$mode-$policy"
dir="$base/$run"
[[ ! -e "$dir" ]] || { echo "Refusing to overwrite $dir"; exit 1; }
mkdir -p "$dir/kernel-snapshots"
exec 9>"$root/result/measured-cat-20260907/batch.lock"
flock -n 9 || exit 1
exec 8>"$root/result/online-mix-20260907/device.lock"
flock -n 8 || exit 1
loaded=0
collector=
workload_pid=
marker="varmail-$run-$$"
printf '\n### varmail-20260908 %s — started %s\n\n- Policy=%s, duration=%ss,24000 files,gamma mean256KiB/shape1.5,16threads,append16KiB,read1MiB,prealloc80%%.\n- Command `bash script/varmail-20260908.sh %s %s`; source/module/tool hashes in `result/varmail-20260908/run-inputs.sha256`; run environment and raw evidence `%s`.\n- Buffered fsync workload; cache drop disabled for every policy. Generated fileset size recorded; Filebench randomization control recorded in dependency notes.\n' "$run" "$(date -Is)" "$policy" "$seconds" "$mode" "$policy" "$dir" >> "$journal"
finish() {
    rc=$?
    trap - EXIT
    set +e
    if [[ -n "$workload_pid" ]]; then kill -TERM "$workload_pid" 2>/dev/null; wait "$workload_pid"; fi
    if ((loaded)); then
        if [[ -w "$control" ]]; then
            if [[ $(field "$control" active) == 1 ]]; then printf 'stop\n' > "$control" || rc=1; fi
            cat "$control" > "$dir/final-control.txt" || rc=1
        fi
        if mountpoint -q "$root/mnt"; then sudo -n umount "$root/mnt" || rc=1; fi
        sudo -n rmmod nvmev || rc=1
    fi
    if [[ -n "$collector" ]]; then kill "$collector"; wait "$collector"; fi
    sudo -n dmesg --color=never > "$dir/kernel-final.log" || rc=1
    awk -v s="$marker" '!seen[$0]++ {if(index($0,s))on=1;if(on)print}' "$dir"/kernel-snapshots/*.log "$dir/kernel-final.log" > "$dir/kernel.log" || rc=1
    if [[ "$rc" == 0 && "$policy" == online ]]; then
        grep -q 'WATGC_V2 sample' "$dir/kernel.log" || rc=1
    fi
    printf '\n- Finished %s; %s exit=%s; evidence `%s`. Module/mount cleanup attempted.\n' "$(date -Is)" "$run" "$rc" "$dir" >> "$journal"
    if [[ -f "$dir/summary.txt" ]]; then sed 's/^/- /' "$dir/summary.txt" >> "$journal"; fi
    printf '%s\n' "$rc" > "$dir/exit-code.txt"
    echo "VARMAIL $run exit=$rc"
    exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'printf "FAIL line=%s command=%s\n" "$LINENO" "$BASH_COMMAND" >&2' ERR
if [[ -e /sys/module/nvmev ]] || mountpoint -q "$root/mnt"; then echo 'Device in use'; exit 1; fi
if compgen -G '/sys/class/nvme/nvme*' >/dev/null; then echo 'Existing NVMe controller'; exit 1; fi
sha256sum --check --status "$base/run-inputs.sha256"
filebench=$(< "$base/filebench-path.txt")
[[ -x "$filebench" ]]
{
    date -Is
    uname -a
    cat /proc/cmdline
    cat "$root/buildoutput/nvmev-$tag.build-info.txt"
    sha256sum "$root/buildoutput/nvmev-$tag.ko" "$filebench"
    lscpu
    free -h
    for cpu in 1 2; do
        file="/sys/devices/system/cpu/cpu$cpu/cpufreq/scaling_governor"
        if [[ -r "$file" ]]; then printf '%s=' "$file"; cat "$file"; fi
    done
} > "$dir/environment.txt"
sed -e "s/@RUN_ID@/$run/" -e "s/@SECONDS@/$seconds/" "$root/workloads/varmail-compare.f" > "$dir/workload.f"
sha256sum "$dir/workload.f" > "$dir/workload.sha256"
printf '%s\n' "$marker" | sudo -n tee /dev/kmsg >/dev/null
(
    sleeper=
    trap 'if [[ -n "$sleeper" ]]; then kill "$sleeper" 2>/dev/null || true; fi; exit 0' TERM INT
    index=0
    while true; do
        printf -v snapshot '%s/kernel-snapshots/%06d.log' "$dir" "$index"
        sudo -n dmesg --color=never > "$snapshot" || exit 1
        index=$((index+1))
        sleep 30 & sleeper=$!
        wait "$sleeper"
    done
) & collector=$!
sudo -n insmod "$root/buildoutput/nvmev-$tag.ko" memmap_start=4G memmap_size=8192M cpus=1,2 measurement_manual=1 measurement_uid="$(id -u)"
loaded=1
for attempt in {1..50}; do
    [[ -b /dev/nvme0n1 && -w "$control" ]] && break
    sleep 0.2
done
[[ -b /dev/nvme0n1 && -w "$control" ]]
grep -q CSL_Virt /sys/class/nvme/nvme0/model
cat /sys/class/nvme/nvme0/model /sys/class/block/nvme0n1/size > "$dir/device.txt"
sudo -n mkfs.ext4 /dev/nvme0n1 > "$dir/mkfs.txt" 2>&1
sudo -n mount -o nodiscard /dev/nvme0n1 "$root/mnt"
sudo -n chown -R oy:oy "$root/mnt"
fio --name=preset --filename="$root/mnt/preset.dat" --size=6G --rw=write --bs=128k --direct=1 --ioengine=libaio --iodepth=32 --end_fsync=1 --output-format=json --output="$dir/preset.json"
jq -e 'all(.jobs[]; .error==0)' "$dir/preset.json" >/dev/null
# This exact file was generated above on the verified new virtual namespace.
rm -- "$root/mnt/preset.dat"
sync -f "$root/mnt"
mkdir -p "$root/mnt/filebench"
timeout --signal=TERM --kill-after=15 "$((seconds+600))" setarch "$(uname -m)" -R "$filebench" -f "$dir/workload.f" > "$dir/filebench.log" 2>&1 & workload_pid=$!
while kill -0 "$workload_pid" 2>/dev/null; do
    if [[ -e "$dir/barrier-failed.txt" ]]; then echo 'Measurement barrier failed'; exit 1; fi
    sleep 1
done
wait "$workload_pid"
workload_pid=
[[ -s "$dir/measurement-start.txt" ]]
grep -q 'IO Summary:' "$dir/filebench.log"
if grep -Ei 'aborting|no space left|segmentation fault|failed|ERROR' "$dir/filebench.log"; then exit 1; fi
sync -f "$root/mnt"
stop_before=$(sectors)
printf 'stop\n' > "$control"
after=$(sectors)
[[ "$stop_before" == "$after" ]]
date -Is > "$dir/measurement-end.txt"
cat "$control" > "$dir/stopped.txt"
before=$(< "$dir/before-sectors.txt")
bytes=$(field "$dir/stopped.txt" host_bytes)
host=$(field "$dir/stopped.txt" host_pages)
gc=$(field "$dir/stopped.txt" gc_pages)
[[ "$bytes" == "$(((after-before)*512))" && "$bytes" -gt 0 && "$gc" -gt 0 && $(field "$dir/stopped.txt" active) == 0 ]]
awk -v h="$host" -v g="$gc" -v b="$bytes" 'BEGIN{printf "host_bytes=%.0f host_pages=%.0f gc_pages=%.0f page_WAF=%.9f FTL_page_bytes_per_host_byte=%.9f\n",b,h,g,1+g/h,(h+g)*4096/b}' > "$dir/summary.txt"
grep 'IO Summary:' "$dir/filebench.log" >> "$dir/summary.txt"
