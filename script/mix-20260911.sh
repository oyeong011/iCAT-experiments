#!/usr/bin/env bash
# Mix experiment: phase A = fio test4 (fixed payload) -> delete file -> phase B = YCSB sqlite workload A.
# Usage: mix-20260911.sh <smoke|main> <fixed47|online>
set -Eeuo pipefail
root=/home/oy/iCAT
base="$root/result/mix-20260911"
journal="$root/EXPERIMENT_LOG.md"
control=/proc/nvmevirt_measurement
label=${1:?Use smoke, main, long, t4, mixA, mixB or mixC}; policy=${2:?Use fixed47 or online}; rep=${3:-1}
case "$policy" in
    fixed47) module="$root/buildoutput/nvmev-varmail-20260908-fixed47.ko";;
    online)  module="$root/buildoutput/nvmev-online-mix-20260907.ko";;
    fixed10) module="$root/buildoutput/nvmev-fixed10.ko";;
    fixed37) module="$root/buildoutput/nvmev-fixed37.ko";;
    greedy)  module="$root/buildoutput/nvmev-greedy-m.ko";;
    fixed50) module="$root/buildoutput/nvmev-fixed50.ko";;
    *) exit 2;;
esac
# test4 payload: 24M writes = 600 s at 40k IOPS (hot:warm:cold = 6:3:1). smoke = 1/10.
case "$label" in
    smoke) scale=10; RECORDS=20000; OPS=20000;;
    main)  scale=1;  RECORDS=4000000; OPS=1000000;;
    long)  scale=1;  RECORDS=4000000; OPS=10000000;;
    t4)    scale=1;  RECORDS=0; OPS=0;;   # single workload test4 only, no phase B; rep selects seed
    mixA|mixB) scale=1; RECORDS=600000; OPS=4000000;;
    mixC)  scale=1;  RECORDS=0; OPS=0;;   # plan A: keep phase-A file (no zombie data); 600k records (~0.8 GiB) fits the remaining ~1.5 GiB
    *) exit 2;;
esac
mult=1; [[ "$label" != long ]] || mult=6   # long: phase A 6x payload (3600 s) so the learner can exploit after its 600 s sweep
[[ -z "${SMOKE:-}" ]] || { scale=$((scale*10)); RECORDS=20000; OPS=20000; }   # SMOKE=1: 1/10 payload, tiny DB
export HOT_IO=$((58982400000*mult/scale)) WARM_IO=$((29491200000*mult/scale)) COLD_IO=$((9830400000*mult/scale))
export SEED_HOT=$((20260910+rep)) SEED_WARM=$((20261010+rep)) SEED_COLD=$((20261110+rep))
dir="$base/$label-$policy"; [[ "$label" != t4 && "$label" != mix[ABC] ]] || dir="$base/$label-$policy-rep$rep"
[[ -z "${SMOKE:-}" ]] || dir="$dir-smoke"
[[ ! -e "$dir" ]] || { echo "Refusing to overwrite $dir" >&2; exit 1; }
mkdir -p "$dir"
exec 9>"$base/device.lock"; flock -n 9 || exit 1
export FIO_TARGET="$root/mnt/test.dat"
ycsb=/home/oy/YCSB/ycsb-0.17.0
db="$root/mnt/ycsb.db"
loaded=0; collector=; dc=
marker="mix-$label-$policy-$$"
printf '\n### mix-20260911 %s %s — started %s\n\n- Phase A fio test4 fixed payload (%s/%s/%s bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (%s records, %s ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `%s`.\n- Command: `bash script/mix-20260911.sh %s %s`; evidence `result/mix-20260911/%s-%s/`.\n' "$label" "$policy" "$(date -Is)" "$HOT_IO" "$WARM_IO" "$COLD_IO" "$RECORDS" "$OPS" "$(basename "$module")" "$label" "$policy" "$label" "$policy" >> "$journal"
field() { awk -v key="$2" 'NR==1{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]==key)print a[2]}}' "$1"; }
sectors() { awk '{print $7}' /sys/class/block/nvme0n1/stat; }
kmsg() { printf '%s %s\n' "$marker" "$*" | sudo -n tee /dev/kmsg >/dev/null; }
phase_waf() { # phase_waf <start.txt> <end.txt>
    awk -v h0="$(field "$1" host_pages)" -v g0="$(field "$1" gc_pages)" -v h1="$(field "$2" host_pages)" -v g1="$(field "$2" gc_pages)" \
        'BEGIN{h=h1-h0;g=g1-g0; printf "host_pages=%d gc_pages=%d WAF=%s", h, g, (h>0)?sprintf("%.6f",1+g/h):"N/A"}'
}
finish() {
    rc=$?; trap - EXIT ERR; set +e
    [[ -z "$dc" ]] || { rm -f "$dir/dc.flag"; wait "$dc" 2>/dev/null; }
    if ((loaded)); then
        if [[ -w "$control" ]]; then
            [[ $(field "$control" active) != 1 ]] || printf 'stop\n' > "$control" || rc=1
            cat "$control" > "$dir/final-control.txt" || rc=1
        fi
        if mountpoint -q "$root/mnt"; then sudo -n umount "$root/mnt" || rc=1; fi
        sudo -n rmmod nvmev || rc=1
    fi
    [[ -z "$collector" ]] || { kill "$collector"; wait "$collector"; }
    sudo -n dmesg --color=never > "$dir/kernel-final.log" || rc=1
    awk -v s="$marker" '!seen[$0]++ {if(index($0,s))on=1; if(on)print}' "$dir"/kernel-snapshots/*.log "$dir/kernel-final.log" > "$dir/kernel.log" || rc=1
    if [[ "$rc" == 0 && "$policy" == online ]]; then
        for part in 0 1 2 3; do grep -Eq "WATGC_V2 sample .*part=$part " "$dir/kernel.log" || rc=1; done
    fi
    printf '\n- Finished %s; %s %s exit=%s; evidence `%s`; cleanup attempted.\n' "$(date -Is)" "$label" "$policy" "$rc" "$dir" >> "$journal"
    [[ ! -f "$dir/summary.txt" ]] || sed 's/^/- /' "$dir/summary.txt" >> "$journal"
    printf '%s\n' "$rc" > "$dir/exit-code.txt"
    echo "MIX $label $policy exit=$rc"
    exit "$rc"
}
trap finish EXIT; trap 'exit 130' INT; trap 'exit 143' TERM
trap 'printf "FAIL line=%s command=%s\n" "$LINENO" "$BASH_COMMAND" >&2' ERR
if [[ -e /sys/module/nvmev ]] || mountpoint -q "$root/mnt"; then echo 'Device already in use'; exit 1; fi
if compgen -G '/sys/class/nvme/nvme*' >/dev/null; then echo 'Existing NVMe device: refusing initialization'; exit 1; fi
{ date -Is; uname -a; cat /proc/cmdline; fio --version; java -version 2>&1; sqlite3 --version; sha256sum "$module" "$0" "$root/workloads/mix-test4.fio" "$root/workloads/sqlite/workloada"; lscpu; free -h; } > "$dir/environment.txt"
kmsg BEGIN
mkdir -p "$dir/kernel-snapshots"
( exec 9>&-; trap 'kill $sl 2>/dev/null; exit 0' TERM; i=0; while true; do printf -v s '%s/kernel-snapshots/%06d.log' "$dir" "$i"; sudo -n dmesg --color=never > "$s" || exit 1; i=$((i+1)); sleep 30 & sl=$!; wait $sl; done ) & collector=$!
sudo -n insmod "$module" memmap_start=4G memmap_size=8192M cpus=1,2 measurement_manual=1 measurement_uid="$(id -u)"
loaded=1
for _ in {1..50}; do [[ -b /dev/nvme0n1 && -w "$control" ]] && break; sleep 0.2; done
[[ -b /dev/nvme0n1 && -w "$control" ]]
grep -q CSL_Virt /sys/class/nvme/nvme0/model
cat /sys/class/nvme/nvme0/model /sys/class/block/nvme0n1/size > "$dir/device.txt"
sudo -n mkfs.ext4 /dev/nvme0n1 > "$dir/mkfs.txt" 2>&1
sudo -n mount -o nodiscard /dev/nvme0n1 "$root/mnt"
sudo -n chown -R oy:oy "$root/mnt"
# preparation (identical to measured-cat / online-mix)
fio --name=preset --filename="$FIO_TARGET" --size=6G --rw=write --bs=128k --direct=1 --ioengine=libaio --iodepth=32 --end_fsync=1 --output-format=json --output="$dir/preset.json"
fio --name=prepare --filename="$FIO_TARGET" --size=6G --io_size=3G --rw=randwrite --bs=4k --direct=1 --ioengine=libaio --iodepth=32 --rate_iops=10000 --randrepeat=1 --randseed=20260907 --end_fsync=1 --output-format=json --output="$dir/prepare.json"
sync -f "$FIO_TARGET"
jq -s -e 'all(.[]; all(.jobs[]; .error == 0))' "$dir/preset.json" "$dir/prepare.json" >/dev/null
cat "$control" > "$dir/prepared.txt"
[[ $(field "$dir/prepared.txt" host_bytes) == 0 && $(field "$dir/prepared.txt" gc_pages) == 0 ]]
before=$(sectors)
printf 'start\n' > "$control"
cat "$control" > "$dir/started.txt"
# ---- phases. Slot A runs first, slot B second; which workload fills each slot depends on the label.
phase_fio() { # phase_fio <slot> <fio job file>
    local slot=$1 job=$2
    kmsg phase=$slot START; date -Is > "$dir/phase-$slot-start.time"
    cat "$control" > "$dir/phase-$slot-start.txt"
    fio "$root/workloads/$job" --output-format=json --output="$dir/phase-$slot.json"
    sync -f "$FIO_TARGET"
    jq -e 'all(.jobs[]; .error == 0 and .write.io_bytes > 0)' "$dir/phase-$slot.json" >/dev/null
    cat "$control" > "$dir/phase-$slot-end.txt"; date -Is > "$dir/phase-$slot-end.time"
    kmsg phase=$slot END
}
phase_sqlite() { # phase_sqlite <slot>  (same as GitHub sqlite.sh: WAL, batch 1000, drop_caches 4s during run)
    local slot=$1
    cat "$control" > "$dir/phase-$slot-start.txt"
    kmsg phase=$slot START; date -Is > "$dir/phase-$slot-start.time"
    sqlite3 "$db" "PRAGMA page_size=4096; PRAGMA synchronous=NORMAL; PRAGMA journal_mode=WAL;
     CREATE TABLE usertable (YCSB_KEY VARCHAR(255) PRIMARY KEY, FIELD0 TEXT, FIELD1 TEXT, FIELD2 TEXT, FIELD3 TEXT, FIELD4 TEXT, FIELD5 TEXT, FIELD6 TEXT, FIELD7 TEXT, FIELD8 TEXT, FIELD9 TEXT);"
    yc() { (cd "$ycsb" && JAVA_TOOL_OPTIONS="-Xshare:off" bash bin/ycsb.sh "$1" jdbc -s -P "$root/workloads/sqlite/workloada" -p recordcount="$RECORDS" -p operationcount="$OPS" -threads 1 \
            -p db.driver=org.sqlite.JDBC -p db.url="jdbc:sqlite:$db" -p db.user= -p db.passwd= -p db.batchsize=1000 -p jdbc.autocommit=false); }
    kmsg phase=$slot LOAD; yc load > "$dir/ycsb-load.txt" 2>&1
    grep -q '^\[INSERT\], Return=OK, ' "$dir/ycsb-load.txt"
    sync; cat "$control" > "$dir/phase-$slot-loaded.txt"
    touch "$dir/dc.flag"
    ( exec 9>&-; while [[ -e "$dir/dc.flag" ]]; do sleep 4; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; done ) & dc=$!
    kmsg phase=$slot RUN; yc run > "$dir/ycsb-run.txt" 2>&1
    rm -f "$dir/dc.flag"; wait "$dc"; dc=
    grep -q '^\[UPDATE\], Return=OK, ' "$dir/ycsb-run.txt"
    sync; cat "$control" > "$dir/phase-$slot-end.txt"; date -Is > "$dir/phase-$slot-end.time"
    kmsg phase=$slot END
}
skip_slot() { for f in start loaded end; do cp "$dir/phase-A-end.txt" "$dir/phase-B-$f.txt"; done; : > "$dir/ycsb-load.txt"; : > "$dir/ycsb-run.txt"; }
: > "$dir/ycsb-load.txt"; : > "$dir/ycsb-run.txt"
case "$label" in
    t4)    A_NAME=test4; B_NAME=none;     phase_fio A mix-test4.fio; skip_slot;;
    mixB)  A_NAME=sqlite-a; B_NAME=test4; phase_sqlite A; phase_fio B mix-test4.fio;;          # app first, then fio; fio file kept from preset
    mixC)  A_NAME=test3; B_NAME=test4;    HOT_IO=$((HOT_IO/4)) WARM_IO=$((WARM_IO/4)) COLD_IO=$((COLD_IO/4)) phase_fio A mix-test3.fio; phase_fio B mix-test4.fio;;  # test3 = 1/4 IOPS, 1/4 payload → same 600 s # same layout, IOPS x4: overwrite time axis shifts
    mixA)  A_NAME=test4; B_NAME=sqlite-a; phase_fio A mix-test4.fio; phase_sqlite B;;           # fio file kept: no deleted-but-valid data
    *)     A_NAME=test4; B_NAME=sqlite-a; phase_fio A mix-test4.fio
           rm -f "$FIO_TARGET"; sync   # smoke/main/long: delete fio file (no discard, FTL keeps it valid)
           phase_sqlite B;;
esac
# ---- stop
stop_before=$(sectors); printf 'stop\n' > "$control"; after=$(sectors)
[[ "$stop_before" == "$after" ]]
cat "$control" > "$dir/stopped.txt"
host=$(field "$dir/stopped.txt" host_pages); gc=$(field "$dir/stopped.txt" gc_pages); bytes=$(field "$dir/stopped.txt" host_bytes)
[[ "$bytes" == "$(((after-before)*512))" && "$gc" -gt 0 ]]   # buffered sqlite writes: host_pages*4096 == bytes is NOT enforced
{
    awk -v h="$host" -v g="$gc" -v b="$bytes" 'BEGIN{printf "total host_bytes=%.0f host_pages=%.0f gc_pages=%.0f WAF=%.6f\n",b,h,g,1+g/h}'
    printf 'phaseA(%s) %s\n' "$A_NAME" "$(phase_waf "$dir/phase-A-start.txt" "$dir/phase-A-end.txt")"
    printf 'phaseB(%s) %s\n' "$B_NAME" "$(phase_waf "$dir/phase-B-start.txt" "$dir/phase-B-end.txt")"
    for sl in A B; do [[ -f "$dir/phase-$sl-loaded.txt" ]] && printf 'phase%s-load %s\nphase%s-run %s\n' "$sl" "$(phase_waf "$dir/phase-$sl-start.txt" "$dir/phase-$sl-loaded.txt")" "$sl" "$(phase_waf "$dir/phase-$sl-loaded.txt" "$dir/phase-$sl-end.txt")"; done
    printf 'ycsb-load %s\nycsb-run %s\n' "$(grep -m1 'Throughput' "$dir/ycsb-load.txt")" "$(grep -m1 'Throughput' "$dir/ycsb-run.txt")"
} > "$dir/summary.txt"
cat "$dir/summary.txt"
