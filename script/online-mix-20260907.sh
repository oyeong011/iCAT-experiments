#!/usr/bin/env bash
set -Eeuo pipefail
root=/home/oy/iCAT
base="$root/result/online-mix-20260907"
journal="$root/EXPERIMENT_LOG.md"
control=/proc/nvmevirt_measurement
module="$root/buildoutput/nvmev-online-mix-20260907.ko"
label=${1:?Use smoke or main}
case "$label" in smoke) export PHASE_SECONDS=30;; main) export PHASE_SECONDS=3600;; *) exit 2;; esac
dir="$base/$label"
[[ ! -e "$dir" ]] || { echo "Refusing to overwrite $dir" >&2; exit 1; }
mkdir -p "$dir"
exec 9>"$base/device.lock"
flock -n 9 || exit 1
exec 8>"$root/result/measured-cat-20260907/batch.lock"
flock -n 8 || { echo 'Existing CAT batch owns the device'; exit 1; }
export FIO_TARGET="$root/mnt/test.dat"
loaded=0
collector=
marker="online-mix-$label-$$"
printf '\n### online-mix-20260907 %s — started %s\n\n- Online discounted UCB; last-invalidation Age; A(front hot)→B(back hot), %s seconds/phase; total target 40k 4KiB IOPS.\n- Command: `bash script/online-mix-20260907.sh %s`; evidence `result/online-mix-20260907/%s/`.\n- Fresh device, 6GiB sequential + 3GiB uniform preparation; measurement and cold learner start after preparation; no learner reset between phases.\n' "$label" "$(date -Is)" "$PHASE_SECONDS" "$label" "$label" >> "$journal"
finish() {
    rc=$?
    trap - EXIT
    set +e
    if ((loaded)); then
        if [[ -w "$control" ]]; then
            if [[ $(field /proc/nvmevirt_measurement active) == 1 ]]; then
                printf 'stop\n' > "$control" || rc=1
            fi
            cat "$control" > "$dir/final-control.txt" || rc=1
        fi
        if mountpoint -q "$root/mnt"; then sudo -n umount "$root/mnt" || rc=1; fi
        sudo -n rmmod nvmev || rc=1
    fi
    if [[ -n "$collector" ]]; then kill "$collector"; wait "$collector"; fi
    sudo -n dmesg --color=never > "$dir/kernel-final.log" || rc=1
    awk -v s="$marker" '!seen[$0]++ {if(index($0,s))on=1; if(on)print}' "$dir"/kernel-snapshots/*.log "$dir/kernel-final.log" > "$dir/kernel.log" || rc=1
    if [[ "$rc" == 0 ]]; then
        for part in 0 1 2 3; do
            if ! grep -Eq "WATGC_V2 sample .*part=$part " "$dir/kernel.log"; then rc=1; fi
        done
        if ! awk '/WATGC_V2 sample / {for(i=1;i<=NF;i++){split($i,a,"=");v[a[1]]=a[2]} seen[v["part"] SUBSEP v["evaluated"]]=1; expected=int((1+v["gc_pages"]/v["host"])*65536); delta=v["waf_q16"]-expected;if(delta< -1 || delta>1)bad=1} END {for(k in seen){split(k,a,SUBSEP);n[a[1]]++}for(p=0;p<4;p++)if(n[p]<2)bad=1;exit(bad)}' "$dir/kernel.log"; then rc=1; fi
    fi
    printf '\n- Finished %s; %s exit=%s; evidence `%s`; module/mount cleanup attempted.\n' "$(date -Is)" "$label" "$rc" "$dir" >> "$journal"
    if [[ -f "$dir/summary.txt" ]]; then sed 's/^/- /' "$dir/summary.txt" >> "$journal"; fi
    printf '%s\n' "$rc" > "$dir/exit-code.txt"
    echo "ONLINE MIX $label exit=$rc"
    exit "$rc"
}
field() { awk -v key="$2" 'NR==1{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]==key)print a[2]}}' "$1"; }
sectors() { awk '{print $7}' /sys/class/block/nvme0n1/stat; }
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'printf "FAIL line=%s command=%s\n" "$LINENO" "$BASH_COMMAND" >&2' ERR
if [[ -e /sys/module/nvmev ]] || mountpoint -q "$root/mnt"; then echo 'Device already in use'; exit 1; fi
if compgen -G '/sys/class/nvme/nvme*' >/dev/null; then echo 'Existing NVMe device: refusing initialization'; exit 1; fi
sha256sum --check --status "$base/run-inputs.sha256"
{
    date -Is
    uname -a
    cat /proc/cmdline
    fio --version
    sha256sum "$module"
    lscpu
    free -h
    for cpu in 1 2; do
        for key in scaling_governor scaling_cur_freq; do
            file="/sys/devices/system/cpu/cpu$cpu/cpufreq/$key"
            if [[ -r "$file" ]]; then printf '%s=' "$file"; cat "$file"; fi
        done
    done
} > "$dir/environment.txt"
printf '%s\n' "$marker" | sudo -n tee /dev/kmsg >/dev/null
mkdir -p "$dir/kernel-snapshots"
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
sudo -n insmod "$module" memmap_start=4G memmap_size=8192M cpus=1,2 measurement_manual=1 measurement_uid="$(id -u)"
loaded=1
for attempt in {1..50}; do
    [[ -b /dev/nvme0n1 && -w "$control" ]] && break
    sleep 0.2
done
[[ -b /dev/nvme0n1 && -w "$control" ]]
grep -q CSL_Virt /sys/class/nvme/nvme0/model
cat /sys/class/nvme/nvme0/model /sys/class/block/nvme0n1/size > "$dir/device.txt"
sudo -n dmesg --color=never | awk -v s="$marker" 'index($0,s){on=1}on' > "$dir/init-kernel.log"
grep -q 'WATGC_V2 init' "$dir/init-kernel.log"
sudo -n mkfs.ext4 /dev/nvme0n1 > "$dir/mkfs.txt" 2>&1
sudo -n mount -o nodiscard /dev/nvme0n1 "$root/mnt"
sudo -n chown -R oy:oy "$root/mnt"
findmnt "$root/mnt" > "$dir/mount.txt"
fio --name=preset --filename="$FIO_TARGET" --size=6G --rw=write --bs=128k --direct=1 --ioengine=libaio --iodepth=32 --end_fsync=1 --output-format=json --output="$dir/preset.json"
fio --name=prepare --filename="$FIO_TARGET" --size=6G --io_size=3G --rw=randwrite --bs=4k --direct=1 --ioengine=libaio --iodepth=32 --rate_iops=10000 --randrepeat=1 --randseed=20260907 --end_fsync=1 --output-format=json --output="$dir/prepare.json"
sync -f "$FIO_TARGET"
jq -s -e 'all(.[]; all(.jobs[]; .error == 0))' "$dir/preset.json" "$dir/prepare.json" >/dev/null
cat "$control" > "$dir/prepared.txt"
[[ $(field "$dir/prepared.txt" host_bytes) == 0 && $(field "$dir/prepared.txt" gc_pages) == 0 ]]
sudo -n dmesg --color=never | awk -v s="$marker" 'index($0,s){on=1}on' > "$dir/prepared-kernel.log"
if grep -q 'WATGC_V2 sample' "$dir/prepared-kernel.log"; then echo 'Learning ran during preparation'; exit 1; fi
before=$(sectors)
printf 'start\n' > "$control"
[[ "$before" == "$(sectors)" ]]
cat "$control" > "$dir/started.txt"
[[ $(field "$dir/started.txt" host_bytes) == 0 ]]
for phase in A B; do
    if [[ "$phase" == A ]]; then
        export FRONT_IOPS=32000 BACK_IOPS=8000 FRONT_SEED=20260911 BACK_SEED=20260912
    else
        export FRONT_IOPS=8000 BACK_IOPS=32000 FRONT_SEED=20260913 BACK_SEED=20260914
    fi
    printf '%s phase=%s front_iops=%s back_iops=%s seconds=%s\n' "$(date -Is)" "$phase" "$FRONT_IOPS" "$BACK_IOPS" "$PHASE_SECONDS" | tee -a "$dir/phases.txt"
    printf '%s phase=%s START\n' "$marker" "$phase" | sudo -n tee /dev/kmsg >/dev/null
    cat "$control" > "$dir/phase-$phase-start.txt"
    fio "$root/workloads/online-mix-phase.fio" --output-format=json --output="$dir/phase-$phase.json"
    sync -f "$FIO_TARGET"
    jq -e 'all(.jobs[]; .error == 0 and .write.io_bytes > 0)' "$dir/phase-$phase.json" >/dev/null
    cat "$control" > "$dir/phase-$phase-end.txt"
    printf '%s phase=%s END\n' "$marker" "$phase" | sudo -n tee /dev/kmsg >/dev/null
done
stop_before=$(sectors)
printf 'stop\n' > "$control"
after=$(sectors)
[[ "$stop_before" == "$after" ]]
cat "$control" > "$dir/stopped.txt"
host=$(field "$dir/stopped.txt" host_pages)
gc=$(field "$dir/stopped.txt" gc_pages)
bytes=$(field "$dir/stopped.txt" host_bytes)
[[ "$bytes" == "$(((after-before)*512))" && "$bytes" == "$((host*4096))" && "$gc" -gt 0 ]]
[[ $(field "$dir/stopped.txt" active) == 0 ]]
payload=$(jq -s '[.[].jobs[].write.io_bytes] | add' "$dir/phase-A.json" "$dir/phase-B.json")
[[ "$bytes" -ge "$payload" ]]
awk -v h="$host" -v g="$gc" -v b="$bytes" 'BEGIN{printf "host_bytes=%.0f host_pages=%.0f gc_pages=%.0f WAF=%.9f\n",b,h,g,1+g/h}' > "$dir/summary.txt"
printf 'before_sectors=%s after_sectors=%s\n' "$before" "$after" >> "$dir/summary.txt"
