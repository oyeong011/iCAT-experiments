#!/usr/bin/env bash
set -Eeuo pipefail
root=/home/oy/iCAT
tag=${1:?Module tag required}
label=${2:-$tag}
[[ "$label" =~ ^[a-zA-Z0-9_-]+$ ]] || exit 1
dir="$root/result/measurement-control-20260907/$label"
control=/proc/nvmevirt_measurement
target="$root/mnt/test.dat"
[[ ! -e "$dir" ]] || exit 1
mkdir -p "$dir"
journal="$root/EXPERIMENT_LOG.md"
printf '\n### Measurement validation %s — started %s\n\n- Explicit mode, Age=%s; fresh ext4, 6 GiB preset, 3 GiB random preparation, measured 1 GiB, stopped 256 MiB, second epoch 128 MiB. Single fio job, 4 KiB direct, fixed seed 20260907, no rate limit.\n- Evidence: `result/measurement-control-20260907/%s/`\n' "$label" "$(date -Is)" "${MEASUREMENT_AGE_DESCRIPTION:-CREATE}" "$label" >> "$journal"
loaded=0
start="measurement-check-$tag-$$"
finish() {
    rc=$?
    trap - EXIT
    if ((loaded)); then
        if mountpoint -q "$root/mnt"; then sudo -n umount "$root/mnt" || rc=1; fi
        sudo -n rmmod nvmev || rc=1
    fi
    sudo -n dmesg --color=never | awk -v s="$start" 'index($0,s){on=1}on' > "$dir/kernel.log"
    printf '\n- Finished %s; validation exit=%s; evidence `%s`\n' "$(date -Is)" "$rc" "$dir" >> "$journal"
    echo "VALIDATION $tag exit=$rc"
    exit "$rc"
}
trap finish EXIT
[[ ! -e /sys/module/nvmev ]] && ! mountpoint -q "$root/mnt"
if compgen -G '/sys/class/nvme/nvme*' >/dev/null; then exit 1; fi
{
    date -Is
    uname -a
    cat /proc/cmdline
    fio --version
    sha256sum "$root/buildoutput/nvmev-$tag.ko"
    cat "$root/buildoutput/nvmev-$tag.build-info.txt"
    lscpu
    free -h
} > "$dir/environment.txt"
printf '%s\n' "$start" | sudo -n tee /dev/kmsg >/dev/null
sudo -n insmod "$root/buildoutput/nvmev-$tag.ko" memmap_start=4G memmap_size=8192M cpus=1,2 measurement_manual=1 measurement_uid="$(id -u)"
loaded=1
for attempt in {1..50}; do
    [[ -b /dev/nvme0n1 && -e "$control" ]] && break
    sleep 0.2
done
[[ -b /dev/nvme0n1 && -w "$control" ]]
grep -q CSL_Virt /sys/class/nvme/nvme0/model
sudo -n mkfs.ext4 /dev/nvme0n1 > "$dir/mkfs.txt" 2>&1
sudo -n mount -o nodiscard /dev/nvme0n1 "$root/mnt"
sudo -n chown -R oy:oy "$root/mnt"
field() { awk -v key="$2" 'NR==1{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]==key)print a[2]}}' "$1"; }
sectors() { awk '{print $7}' /sys/class/block/nvme0n1/stat; }
assert_sectors() {
    local actual
    actual=$(sectors)
    if [[ "$1" != "$actual" ]]; then
        printf 'Boundary not quiet: expected_sectors=%s actual_sectors=%s\n' "$1" "$actual" >&2
        cat "$control" >&2
        return 1
    fi
}
io() {
    fio --name="$1" --filename="$target" --size=6G --io_size="$2" --rw="$3" \
        --bs="$4" --direct=1 --ioengine=libaio --iodepth=32 --randrepeat=1 \
        --randseed=20260907 --end_fsync=1 --output-format=json --output="$dir/$1.json"
    jq -e 'all(.jobs[]; .error == 0)' "$dir/$1.json" >/dev/null
    sync -f "$target"
}
io preset 6G write 128k
io prepare 3G randwrite 4k
cat "$control" > "$dir/prepared.txt"
[[ $(field "$dir/prepared.txt" host_bytes) == 0 && $(field "$dir/prepared.txt" gc_pages) == 0 ]]
before=$(sectors)
printf 'start\n' > "$control"
assert_sectors "$before"
cat "$control" > "$dir/started.txt"
[[ $(field "$dir/started.txt" epoch) == 1 && $(field "$dir/started.txt" host_pages) == 0 ]]
if printf 'start\n' > "$control" 2> "$dir/duplicate-start.txt"; then exit 1; fi
if printf 'invalid\n' > "$control" 2> "$dir/invalid-command.txt"; then exit 1; fi
assert_sectors "$before"
io measured 1G randwrite 4k
stop_before=$(sectors)
printf 'stop\n' > "$control"
after=$(sectors)
assert_sectors "$stop_before"
cat "$control" > "$dir/stopped.txt"
bytes=$(field "$dir/stopped.txt" host_bytes)
pages=$(field "$dir/stopped.txt" host_pages)
gc=$(field "$dir/stopped.txt" gc_pages)
[[ "$bytes" == "$(((after-before)*512))" && "$bytes" == "$((pages*4096))" ]]
[[ "$bytes" -ge 1073741824 && "$gc" -gt 0 ]]
awk 'NR>1{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]=="host_pages")h+=a[2];if(a[1]=="gc_pages")g+=a[2]}}END{print h,g}' "$dir/stopped.txt" > "$dir/partition-sums.txt"
read -r sum_host sum_gc < "$dir/partition-sums.txt"
[[ "$sum_host" == "$pages" && "$sum_gc" == "$gc" ]]
printf 'linux_write_bytes=%s module_host_bytes=%s host_pages=%s gc_pages=%s\n' "$(((after-before)*512))" "$bytes" "$pages" "$gc" | tee "$dir/check.txt"
io after_stop 256M randwrite 4k
cat "$control" > "$dir/after-stop.txt"
cmp "$dir/stopped.txt" "$dir/after-stop.txt"
if printf 'stop\n' > "$control" 2> "$dir/duplicate-stop.txt"; then exit 1; fi
dd if="$target" bs=1M count=1 status=none | sha256sum > "$dir/data-before-start.sha256"
sync -f "$target"
before=$(sectors)
printf 'start\n' > "$control"
assert_sectors "$before"
cat "$control" > "$dir/restarted.txt"
[[ $(field "$dir/restarted.txt" epoch) == 2 && $(field "$dir/restarted.txt" host_pages) == 0 && $(field "$dir/restarted.txt" gc_pages) == 0 ]]
printf 'stop\n' > "$control"
dd if="$target" bs=1M count=1 status=none | sha256sum > "$dir/data-after-start.sha256"
cmp "$dir/data-before-start.sha256" "$dir/data-after-start.sha256"
sync -f "$target"
before=$(sectors)
printf 'start\n' > "$control"
assert_sectors "$before"
io second_epoch 128M randwrite 4k
stop_before=$(sectors)
printf 'stop\n' > "$control"
after=$(sectors)
assert_sectors "$stop_before"
cat "$control" > "$dir/second-stopped.txt"
[[ $(field "$dir/second-stopped.txt" host_bytes) == "$(((after-before)*512))" ]]
echo 'PASS: preparation excluded, block bytes match, GC included, stopped counters frozen, restart resets, sample data preserved.'
