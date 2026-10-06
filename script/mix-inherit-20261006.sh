#!/usr/bin/env bash
# 10-06 inheritance mix (copy of mix-20260911.sh; the original was left untouched because a run was executing it).
# mixV: mixT's 9-phase order, but no permanent 6 GiB FIO file. At every switch the outgoing workload's files are deleted
# (nodiscard: the FTL still holds them) and the incoming workload allocates on the freed LBAs, i.e. it overwrites the
# previous workload's data. Before measuring, the whole file system is written once and deleted, so every LBA holds data.
# Usage: mix-inherit-20261006.sh mixV <policy> [rep]
set -Eeuo pipefail
root=/home/oy/iCAT
base="${MIX_BASE:-$root/result/inherit-20261006}"   # second PC writes to its own dir
journal="${MIX_JOURNAL:-$root/EXPERIMENT_LOG.md}"
control=/proc/nvmevirt_measurement
label=${1:?Use smoke, main, long, t4, or mixA/B/C/D/F/G/H/J/K/L/M/O/P/Q}; policy=${2:?Use fixed47 or online}; rep=${3:-1}
case "$policy" in
    fixed47) module="$root/buildoutput/nvmev-varmail-20260908-fixed47.ko";;
    online)  module="$root/buildoutput/nvmev-online-mix-20260907.ko";;
    onlinev2) module="$root/buildoutput/nvmev-online-v2.ko";;   # v1 + 6x reward window
    onlinev3) module="$root/buildoutput/nvmev-online-v3.ko";;   # v2 src + window x2, k=2 arms skipped (45), 1 visit, no probe after settle, drift 25%
    onlinev4) module="$root/buildoutput/nvmev-online-v4.ko";;   # v3 + online elimination (15%) + neighbour probe every 8 + reset restores survivors+neighbours
    onlinev5) module="$root/buildoutput/nvmev-online-v5.ko";;   # 10-05: v4 + GC-capped windows used (>= 64 MiB host) instead of discarded
    onlinev6) module="$root/buildoutput/nvmev-online-v6.ko";;   # 10-05: v5 + change detection in any state (pauses elimination; 3 far samples -> reset with all arms)
    onlinev3k2) module="$root/buildoutput/nvmev-online-v3k2.ko";;   # ablation: v3 with k=2 arms back (60 arms)
    onlinev3probe) module="$root/buildoutput/nvmev-online-v3probe.ko";;   # ablation: v3 with v1 post-settle probing back
    onlinev3win1) module="$root/buildoutput/nvmev-online-v3win1.ko";;   # ablation
    onlinev3visits3) module="$root/buildoutput/nvmev-online-v3visits3.ko";;   # ablation
    onlinev3drift12) module="$root/buildoutput/nvmev-online-v3drift12.ko";;   # ablation
    onlinev4noelim) module="$root/buildoutput/nvmev-online-v4noelim.ko";;   # ablation
    onlinev4noprobe) module="$root/buildoutput/nvmev-online-v4noprobe.ko";;   # ablation
    onlinev4fullreset) module="$root/buildoutput/nvmev-online-v4fullreset.ko";;   # ablation
    fixed10) module="$root/buildoutput/nvmev-fixed10.ko";;
    arm[0-5][0-9]) module="$root/buildoutput/nvmev-$policy.ko";;   # any of the 60 sweep modules
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
    t4|t4long) scale=1;  RECORDS=0; OPS=0;;   # single workload test4 only, no phase B; rep selects seed; t4long = 6x payload (3600 s)
    mixA|mixB|mixG|mixH|mixJ|mixT) scale=1; RECORDS=600000; OPS=4000000;;
    mixV)  scale=1;  RECORDS=600000; OPS=1000000000;;   # no permanent FIO file, so the original 600k DB fits again
    mixP)  scale=1;  RECORDS=250000; OPS=4000000;;   # sqlite then oltp: 600k records + WAL left no room for the oltp fileset (ENOSPC on rep1)
    mixR)  scale=1;  RECORDS=600000; OPS=14000000;;   # test4 -> sqlite-a -> test4, each phase ~24M host pages (sqlite-a run ~1.7 pages/op)
    mixC|mixD|mixF|mixK|mixL|mixM|mixO|mixQ|mixS|mixU)  scale=1;  RECORDS=0; OPS=0;;   # plan A: keep phase-A file (no zombie data); 600k records (~0.8 GiB) fits the remaining ~1.5 GiB
    *) exit 2;;
esac
mult=${MULT:-1}; [[ "$label" != long && "$label" != t4long ]] || mult=6   # MULT=n: every phase n times longer (fio payload and YCSB ops); for phase-length vs learning-time analysis   # long: phase A 6x payload (3600 s) so the learner can exploit after its 600 s sweep
[[ -z "${SMOKE:-}" ]] || { scale=$((scale*10)); RECORDS=20000; OPS=20000; export VM_FILES=2000 VM_RUN=20; }   # SMOKE=1: 1/10 payload, tiny DB
export HOT_IO=$((58982400000*mult/scale)) WARM_IO=$((29491200000*mult/scale)) COLD_IO=$((9830400000*mult/scale))
export SEED_HOT=$((20260910+rep)) SEED_WARM=$((20261010+rep)) SEED_COLD=$((20261110+rep))
dir="$base/$label-$policy"; [[ "$label" != t4 && "$label" != t4long && "$label" != mix[A-Z] ]] || dir="$base/$label-$policy-rep$rep"
[[ -z "${MULT:-}" || "$MULT" == 1 ]] || { dir="$dir-x$MULT"; OPS=$((OPS*MULT)); }
[[ -z "${SMOKE:-}" ]] || dir="$dir-smoke"
[[ ! -e "$dir" ]] || { echo "Refusing to overwrite $dir" >&2; exit 1; }
mkdir -p "$dir"
mkdir -p "$root/result/mix-20260911"; exec 9>"$root/result/mix-20260911/device.lock"   # same lock as the original runner; flock -n 9 || exit 1
export FIO_TARGET="$root/mnt/test.dat"
ycsb=/home/oy/YCSB/ycsb-0.17.0
db="$root/mnt/ycsb.db"
declare -A PN=()   # mixS: phase slot -> workload name
loaded=0; collector=; dc=; series=
marker="mix-$label-$policy-$$"
if [[ "$label" == mixU ]]; then   # 10-05
printf '\n### mix-20260911 %s %s — started %s\n\n- mixU: FIO-Fast and Varmail alternate, 8 time-based phases of %s s (F V F V F V F V). FIO payload x %s/600; Varmail one run per phase. FIO file kept. Module `%s`.\n- Command: `env PH_SECS=%s bash script/mix-20260911.sh %s %s %s`; evidence `%s/`.\n' "$label" "$policy" "$(date -Is)" "${PH_SECS:-4500}" "${PH_SECS:-4500}" "$(basename "$module")" "${PH_SECS:-4500}" "$label" "$policy" "$rep" "${dir#$root/}" >> "$journal"
elif [[ "$label" == mixV ]]; then
printf '\n### inherit-20261006 %s %s — started %s\n\n- mixV (inheritance): 9 time-based phases of %s s — YCSB-A (load %s records) -> OLTP -> Varmail -> YCSB-A (reload) -> YCSB-B (same DB) -> FIO-Fast (6 GiB file written then overwritten, payload x %s/600) -> Varmail -> YCSB-A (reload) -> OLTP. No permanent file: outgoing files deleted at each switch (nodiscard), whole FS written+deleted once before measuring. Extents recorded per switch. Module `%s`.\n- Command: `env PH_SECS=%s bash script/mix-inherit-20261006.sh %s %s %s`; evidence `%s/`.\n' "$label" "$policy" "$(date -Is)" "${PH_SECS:-4000}" "$RECORDS" "${PH_SECS:-4000}" "$(basename "$module")" "${PH_SECS:-4000}" "$label" "$policy" "$rep" "${dir#$root/}" >> "$journal"
elif [[ "$label" == mixT ]]; then   # 10-04: the generic line below describes the original 2-phase mix, not mixT
printf '\n### mix-20260911 %s %s — started %s\n\n- mixT: 9 time-based phases of %s s each — YCSB-A (load %s records) -> OLTP (32 MB x 10 files, %s s x 4 chunks) -> Varmail -> YCSB-A -> YCSB-B -> FIO-Fast test4 (payload x %s/600) -> Varmail -> YCSB-A -> OLTP. FIO file (6 GiB) kept throughout. Module `%s`.\n- Command: `env PH_SECS=%s bash script/mix-20260911.sh %s %s %s`; evidence `%s/`.\n' "$label" "$policy" "$(date -Is)" "${PH_SECS:-4000}" "$RECORDS" "$(( ${PH_SECS:-4000} / 4 ))" "${PH_SECS:-4000}" "$(basename "$module")" "${PH_SECS:-4000}" "$label" "$policy" "$rep" "${dir#$root/}" >> "$journal"
else
printf '\n### mix-20260911 %s %s — started %s\n\n- Phase A fio test4 fixed payload (%s/%s/%s bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (%s records, %s ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `%s`.\n- Command: `bash script/mix-20260911.sh %s %s`; evidence `result/mix-20260911/%s-%s/`.\n' "$label" "$policy" "$(date -Is)" "$HOT_IO" "$WARM_IO" "$COLD_IO" "$RECORDS" "$OPS" "$(basename "$module")" "$label" "$policy" "$label" "$policy" >> "$journal"
fi
field() { awk -v key="$2" 'NR==1{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]==key)print a[2]}}' "$1"; }
nv=  # NVMeVirt controller (nvme0 here, nvme1 on a PC with a real NVMe SSD), found by model after insmod
sectors() { awk '{print $7}' /sys/class/block/${nv}n1/stat; }
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
    [[ -z "${series:-}" ]] || { kill "$series" 2>/dev/null; wait "$series" 2>/dev/null; }
    sudo -n dmesg --color=never > "$dir/kernel-final.log" || rc=1
    awk -v s="$marker" '!seen[$0]++ {if(index($0,s))on=1; if(on)print}' "$dir"/kernel-snapshots/*.log "$dir/kernel-final.log" > "$dir/kernel.log" || rc=1
    if [[ "$rc" == 0 && "$policy" == online* ]]; then
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
for _ in {1..50}; do for c in /sys/class/nvme/nvme*; do grep -qi CSL_Virt "$c/model" 2>/dev/null && nv=$(basename "$c"); done; [[ -n "$nv" && -b /dev/${nv}n1 && -w "$control" ]] && break; sleep 0.2; done
[[ -n "$nv" && -b /dev/${nv}n1 && -w "$control" ]]
# counter time series every 30 s (all policies): lets fixed arms be compared with the learner over time, not just per phase
( exec 9>&-; trap 'kill $sl 2>/dev/null; exit 0' TERM; while true; do printf '%s ' "$(date +%s)"; printf '%s memavail_mb=%s\n' "$(cat "$control" 2>/dev/null | head -1)" "$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)"; sleep 30 & sl=$!; wait $sl; done ) > "$dir/control-series.txt" & series=$!
grep -q CSL_Virt /sys/class/nvme/$nv/model
cat /sys/class/nvme/$nv/model /sys/class/block/${nv}n1/size > "$dir/device.txt"
sudo -n mkfs.ext4 /dev/${nv}n1 > "$dir/mkfs.txt" 2>&1
sudo -n mount -o nodiscard /dev/${nv}n1 "$root/mnt"
sudo -n chown -R oy:oy "$root/mnt"
# preparation. mixV: write the whole file system once, then delete (every LBA now holds data the FTL treats as valid)
ext() { # ext <slot> <tag> <paths...>: physical extents (4 KiB fs blocks; whole-device ext4, so block x 8 = LBA sector)
    local s=$1 t=$2; shift 2; find "$@" -type f -print0 2>/dev/null | xargs -0 -r filefrag -v -b4096 > "$dir/extents-$s-$t.txt" 2>&1 || true; }
if [[ "$label" == mixV ]]; then
    avail=$(df -B1 --output=avail "$root/mnt" | tail -1); fill=$(( (avail - 268435456) / 1048576 ))M
    fio --name=fill --filename="$root/mnt/fill.dat" --size=$fill --rw=write --bs=128k --direct=1 --ioengine=libaio --iodepth=32 --end_fsync=1 --output-format=json --output="$dir/preset.json"
    ext 0 fill "$root/mnt/fill.dat"; rm -f "$root/mnt/fill.dat"; sync; sleep 10; sync
    df -B1 "$root/mnt" > "$dir/fill-df.txt"; cp "$dir/preset.json" "$dir/prepare.json"
else
fio --name=preset --filename="$FIO_TARGET" --size=6G --rw=write --bs=128k --direct=1 --ioengine=libaio --iodepth=32 --end_fsync=1 --output-format=json --output="$dir/preset.json"
fio --name=prepare --filename="$FIO_TARGET" --size=6G --io_size=3G --rw=randwrite --bs=4k --direct=1 --ioengine=libaio --iodepth=32 --rate_iops=10000 --randrepeat=1 --randseed=20260907 --end_fsync=1 --output-format=json --output="$dir/prepare.json"
sync -f "$FIO_TARGET"
jq -s -e 'all(.[]; all(.jobs[]; .error == 0))' "$dir/preset.json" "$dir/prepare.json" >/dev/null
fi
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
    [[ -z "${PRE_FIO:-}" ]] || fio --name=create --filename="$FIO_TARGET" --size=6G --rw=write --bs=128k --direct=1 --ioengine=libaio --iodepth=32 --end_fsync=1 --output-format=json --output="$dir/phase-$slot-create.json"
    fio "$root/workloads/$job" --output-format=json --output="$dir/phase-$slot.json"
    sync -f "$FIO_TARGET"
    jq -e 'all(.jobs[]; .error == 0 and .write.io_bytes > 0)' "$dir/phase-$slot.json" >/dev/null
    cat "$control" > "$dir/phase-$slot-end.txt"; date -Is > "$dir/phase-$slot-end.time"
    kmsg phase=$slot END
}
phase_sqlite() { # phase_sqlite <slot> [workload a|b] [load 1|0]  (same as GitHub sqlite.sh: WAL, batch 1000, drop_caches 4s during run)
    local slot=$1 wl=${2:-a} load=${3:-1}
    cat "$control" > "$dir/phase-$slot-start.txt"
    kmsg phase=$slot START; date -Is > "$dir/phase-$slot-start.time"
    ((load)) && sqlite3 "$db" "PRAGMA page_size=4096; PRAGMA synchronous=NORMAL; PRAGMA journal_mode=WAL;
     CREATE TABLE usertable (YCSB_KEY VARCHAR(255) PRIMARY KEY, FIELD0 TEXT, FIELD1 TEXT, FIELD2 TEXT, FIELD3 TEXT, FIELD4 TEXT, FIELD5 TEXT, FIELD6 TEXT, FIELD7 TEXT, FIELD8 TEXT, FIELD9 TEXT);"
    yc() { (cd "$ycsb" && JAVA_TOOL_OPTIONS="-Xshare:off" bash bin/ycsb.sh "$1" jdbc -s -P "$root/workloads/sqlite/workload$wl" -p recordcount="$RECORDS" -p operationcount="$OPS" ${YCSB_SECS:+-p maxexecutiontime=$YCSB_SECS} -threads 1 \
            -p db.driver=org.sqlite.JDBC -p db.url="jdbc:sqlite:$db" -p db.user= -p db.passwd= -p db.batchsize=1000 -p jdbc.autocommit=false); }
    if ((load)); then
        kmsg phase=$slot LOAD; yc load > "$dir/ycsb-load.txt" 2>&1
        grep -q '^\[INSERT\], Return=OK, ' "$dir/ycsb-load.txt"
        sync; cat "$control" > "$dir/phase-$slot-loaded.txt"
    fi
    touch "$dir/dc.flag"
    ( exec 9>&-; while [[ -e "$dir/dc.flag" ]]; do sleep 4; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; done ) & dc=$!
    kmsg phase=$slot RUN; yc run > "$dir/ycsb-run-$slot.txt" 2>&1; cp "$dir/ycsb-run-$slot.txt" "$dir/ycsb-run.txt"
    rm -f "$dir/dc.flag"; wait "$dc"; dc=
    grep -q '^\[\(UPDATE\|READ\)\], Return=OK, ' "$dir/ycsb-run-$slot.txt"
    sync; cat "$control" > "$dir/phase-$slot-end.txt"; date -Is > "$dir/phase-$slot-end.time"
    kmsg phase=$slot END
}
phase_filebench() { # phase_filebench <slot> <profile> [nfiles] [filesize]: Filebench profile from workloads/filebench, own subdir, 300 s
    local slot=$1 prof=$2 nf=${3:-} fs=${4:-} wl="$dir/$2.f"
    mkdir -p "$root/mnt/filebench"
    sed -e "s#^set \$dir=.*#set \$dir=$root/mnt/filebench#" -e "s#^run .*#run ${VM_RUN:-300}#" "$root/workloads/filebench/$prof.f" > "$wl"
    [[ -z "$nf" ]] || sed -i "s#^set \$nfiles=.*#set \$nfiles=${VM_FILES:-$nf}#" "$wl"
    [[ -z "$fs" ]] || sed -i "s#^set \$filesize=.*#set \$filesize=$fs#" "$wl"   # the 6 GiB preset file stays; only ~1.5 GiB is free
    cat "$control" > "$dir/phase-$slot-start.txt"
    kmsg phase=$slot START; date -Is > "$dir/phase-$slot-start.time"
    # VM_CHUNKS=n (10-03): phase length = VM_RUN x n. filebench's OLTP profile grows ~300 MB/min (aio leak) and stalls the host
    # after ~25 min, so a profile with reusable filesets (oltp) runs as n back-to-back VM_RUN pieces on the same files;
    # others (varmail, no reuse) run once for VM_RUN x n. n=1 is the previous behaviour.
    local c n=${VM_CHUNKS:-1} rt=${VM_RUN:-300}
    grep -q ',reuse' "$wl" || { rt=$(( ${VM_RUN:-300} * n )); n=1; sed -i "s#^run .*#run $rt#" "$wl"; }
    : > "$dir/filebench-$slot.txt"
    for c in $(seq 1 $n); do
        ( exec 9>&-; timeout --signal=TERM --kill-after=15 $(( rt + 900 )) setarch "$(uname -m)" -R "$root/tools/filebench-local/filebench" -f "$wl" ) >> "$dir/filebench-$slot.txt" 2>&1
        kmsg phase=$slot chunk=$c/$n done
    done
    [[ $(grep -c 'IO Summary' "$dir/filebench-$slot.txt") -eq $n ]]
    [[ "$label" != mixV ]] || ext "$slot" files "$root/mnt/filebench"
    rm -rf "$root/mnt/filebench"; sync   # next filebench phase starts from an empty dir (deleted data stays valid in the FTL, as everywhere here)
    cat "$control" > "$dir/phase-$slot-end.txt"; date -Is > "$dir/phase-$slot-end.time"
    kmsg phase=$slot END
}
phase_varmail() { phase_filebench "$1" varmail 24000; }   # 24000 files = the GitHub sweep condition
phase_alternate() { # phase_alternate <slot>: 5 cycles of (fast test4 60 s, slow test3 60 s) — repeated speed changes
    local slot=$1 i
    cat "$control" > "$dir/phase-$slot-start.txt"; kmsg phase=$slot START; date -Is > "$dir/phase-$slot-start.time"
    for i in 1 2 3 4 5; do
        kmsg phase=$slot cycle=$i fast
        HOT_IO=$((HOT_IO/10)) WARM_IO=$((WARM_IO/10)) COLD_IO=$((COLD_IO/10)) fio "$root/workloads/mix-test4.fio" --output-format=json --output="$dir/phase-$slot-c$i-fast.json"
        kmsg phase=$slot cycle=$i slow
        HOT_IO=$((HOT_IO/40)) WARM_IO=$((WARM_IO/40)) COLD_IO=$((COLD_IO/40)) fio "$root/workloads/mix-test3.fio" --output-format=json --output="$dir/phase-$slot-c$i-slow.json"
    done
    sync -f "$FIO_TARGET"; jq -s -e 'all(.[]; all(.jobs[]; .error == 0))' "$dir"/phase-$slot-c*.json >/dev/null
    cat "$control" > "$dir/phase-$slot-end.txt"; date -Is > "$dir/phase-$slot-end.time"; kmsg phase=$slot END
}
phase_ramp() { # phase_ramp <slot>: IOPS ramps 10k -> 20k -> 30k -> 40k -> 50k, 120 s each (gradual drift instead of a step)
    local slot=$1 m
    cat "$control" > "$dir/phase-$slot-start.txt"; kmsg phase=$slot START; date -Is > "$dir/phase-$slot-start.time"
    for m in 1 2 3 4 5; do   # test3 rates x m; payload = 120 s worth
        kmsg phase=$slot step=$m
        HOT_R=$((6000*m)) WARM_R=$((3000*m)) COLD_R=$((1000*m)) HOT_IO=$((6000*m*120*4096/scale)) WARM_IO=$((3000*m*120*4096/scale)) COLD_IO=$((1000*m*120*4096/scale)) \
            fio "$root/workloads/mix-rate.fio" --output-format=json --output="$dir/phase-$slot-step$m.json"
    done
    sync -f "$FIO_TARGET"; jq -s -e 'all(.[]; all(.jobs[]; .error == 0))' "$dir"/phase-$slot-step*.json >/dev/null
    cat "$control" > "$dir/phase-$slot-end.txt"; date -Is > "$dir/phase-$slot-end.time"; kmsg phase=$slot END
}
phase_idle() { # phase_idle <slot> <seconds>: no I/O; block ages keep growing
    local slot=$1 sec=$2
    cat "$control" > "$dir/phase-$slot-start.txt"; kmsg phase=$slot START idle=$sec; date -Is > "$dir/phase-$slot-start.time"
    sleep "$sec"
    cat "$control" > "$dir/phase-$slot-end.txt"; date -Is > "$dir/phase-$slot-end.time"; kmsg phase=$slot END
}
phase_concurrent() { # phase_concurrent <slot>: fio test4 (half payload) in background while sqlite-a runs; both tenants share the device
    local slot=$1 fpid
    cat "$control" > "$dir/phase-$slot-start.txt"
    kmsg phase=$slot START; date -Is > "$dir/phase-$slot-start.time"
    ( exec 9>&-; HOT_IO=$((HOT_IO/2)) WARM_IO=$((WARM_IO/2)) COLD_IO=$((COLD_IO/2)) fio "$root/workloads/mix-test4.fio" --output-format=json --output="$dir/phase-$slot.json" ) & fpid=$!
    sqlite3 "$db" "PRAGMA page_size=4096; PRAGMA synchronous=NORMAL; PRAGMA journal_mode=WAL;
     CREATE TABLE usertable (YCSB_KEY VARCHAR(255) PRIMARY KEY, FIELD0 TEXT, FIELD1 TEXT, FIELD2 TEXT, FIELD3 TEXT, FIELD4 TEXT, FIELD5 TEXT, FIELD6 TEXT, FIELD7 TEXT, FIELD8 TEXT, FIELD9 TEXT);"
    yc() { (cd "$ycsb" && JAVA_TOOL_OPTIONS="-Xshare:off" bash bin/ycsb.sh "$1" jdbc -s -P "$root/workloads/sqlite/workloada" -p recordcount="$RECORDS" -p operationcount="$OPS" -threads 1 \
            -p db.driver=org.sqlite.JDBC -p db.url="jdbc:sqlite:$db" -p db.user= -p db.passwd= -p db.batchsize=1000 -p jdbc.autocommit=false); }
    yc load > "$dir/ycsb-load.txt" 2>&1; grep -q '^\[INSERT\], Return=OK, ' "$dir/ycsb-load.txt"
    touch "$dir/dc.flag"; ( exec 9>&-; while [[ -e "$dir/dc.flag" ]]; do sleep 4; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; done ) & dc=$!
    yc run > "$dir/ycsb-run.txt" 2>&1; rm -f "$dir/dc.flag"; wait "$dc"; dc=
    grep -q '^\[UPDATE\], Return=OK, ' "$dir/ycsb-run.txt"
    wait "$fpid"; sync -f "$FIO_TARGET"
    jq -e 'all(.jobs[]; .error == 0 and .write.io_bytes > 0)' "$dir/phase-$slot.json" >/dev/null
    cat "$control" > "$dir/phase-$slot-end.txt"; date -Is > "$dir/phase-$slot-end.time"
    kmsg phase=$slot END
}
skip_slot() { for f in start loaded end; do cp "$dir/phase-A-end.txt" "$dir/phase-B-$f.txt"; done; : > "$dir/ycsb-load.txt"; : > "$dir/ycsb-run.txt"; }
: > "$dir/ycsb-load.txt"; : > "$dir/ycsb-run.txt"
case "$label" in
    t4|t4long) A_NAME=test4; B_NAME=none; phase_fio A mix-test4.fio; skip_slot;;
    mixB)  A_NAME=sqlite-a; B_NAME=test4; phase_sqlite A; phase_fio B mix-test4.fio;;          # app first, then fio; fio file kept from preset
    mixC)  A_NAME=test3; B_NAME=test4;    HOT_IO=$((HOT_IO/4)) WARM_IO=$((WARM_IO/4)) COLD_IO=$((COLD_IO/4)) phase_fio A mix-test3.fio; phase_fio B mix-test4.fio;;  # test3 = 1/4 IOPS, 1/4 payload → same 600 s # same layout, IOPS x4: overwrite time axis shifts
    mixA)  A_NAME=test4; B_NAME=sqlite-a; phase_fio A mix-test4.fio; phase_sqlite B;;           # fio file kept: no deleted-but-valid data
    mixD)  A_NAME=test4; B_NAME=test3;    phase_fio A mix-test4.fio; HOT_IO=$((HOT_IO/4)) WARM_IO=$((WARM_IO/4)) COLD_IO=$((COLD_IO/4)) phase_fio B mix-test3.fio;;  # reverse of C: slowdown
    mixF)  A_NAME=test4; B_NAME=varmail;  phase_fio A mix-test4.fio; phase_varmail B;;          # fio -> mail server (24000 files)
    mixG)  A_NAME=concurrent-test4+sqlite-a; B_NAME=none; phase_concurrent A; skip_slot;;     # two tenants at once
    mixH)  A_NAME=test3; B_NAME=test4; C_NAME=sqlite-a; HOT_IO=$((HOT_IO/4)) WARM_IO=$((WARM_IO/4)) COLD_IO=$((COLD_IO/4)) phase_fio A mix-test3.fio; phase_fio B mix-test4.fio; phase_sqlite C;;  # three shifts
    mixJ)  A_NAME=sqlite-a; B_NAME=sqlite-b; phase_sqlite A a 1; phase_sqlite B b 0;;         # same DB: update-heavy -> read-heavy
    mixK)  A_NAME=test4-hot512M; B_NAME=test4-hot128M; phase_fio A mix-test4.fio; HOT_SIZE=128M phase_fio B mix-hotsize.fio;;   # same speed, hot region shrinks 4x (locality change)
    mixL)  A_NAME=alternate-fast/slow-x5; B_NAME=none; phase_alternate A; skip_slot;;        # repeated 60 s speed flips
    mixM)  A_NAME=ramp-10k-to-50k; B_NAME=none; phase_ramp A; skip_slot;;                    # gradual drift
    mixO)  A_NAME=oltp; B_NAME=varmail;  phase_filebench A oltp "" 64m; phase_varmail B;;            # two filebench apps
    mixP)  A_NAME=sqlite-a; B_NAME=oltp; phase_sqlite A a 1; phase_filebench B oltp "" 32m;;         # DB -> DB-like app
    mixU)  # 10-05 (user): learning-dynamics run — FIO-Fast and Varmail alternate, 8 phases x PH_SECS (default 4500 s) = 10 h.
           # Both are workloads where the CAT parameters matter (45-combo spread 25.7% / 18.4% > 15% elimination threshold)
           # and GC is moderate, so every phase can show sweep -> narrowing -> (switch) detect -> re-sweep -> narrowing.
           ps_=${PH_SECS:-4500}; i=0
           for w in F V F V F V F V; do sl=$(printf "\\x$(printf %x $((65 + i)))"); i=$((i + 1))
               case $w in
                   V) PN[$sl]=varmail; VM_RUN=$((ps_ / 4)) VM_CHUNKS=4 phase_varmail $sl;;
                   F) PN[$sl]=test4; HOT_IO=$((HOT_IO * ps_ / 600)) WARM_IO=$((WARM_IO * ps_ / 600)) COLD_IO=$((COLD_IO * ps_ / 600)) phase_fio $sl mix-test4.fio;;
               esac
           done; A_NAME=${PN[A]}; B_NAME=${PN[B]};;
    mixV)  # 10-06 (user): workloads inherit each other's LBAs instead of living in separate regions (see header)
           ps_=${PH_SECS:-4000}; i=0; prev=
           for w in YA O V YA YB F V YA O; do sl=$(printf "\\x$(printf %x $((65 + i)))"); i=$((i + 1))
               if [[ $prev == Y* && $w != YB ]]; then ext $sl prevdb "$db" "$db-wal" "$db-shm"; rm -f "$db" "$db-wal" "$db-shm"; sync; sleep 5; sync; fi
               if [[ $prev == F ]]; then rm -f "$FIO_TARGET"; sync; sleep 5; sync; fi
               case $w in
                   YA) PN[$sl]=sqlite-a; YCSB_SECS=$ps_ phase_sqlite $sl a 1; ext $sl files "$db" "$db-wal";;
                   YB) PN[$sl]=sqlite-b; YCSB_SECS=$ps_ phase_sqlite $sl b 0; ext $sl files "$db" "$db-wal";;
                   O)  PN[$sl]=oltp; VM_RUN=$((ps_ / 4)) VM_CHUNKS=4 phase_filebench $sl oltp "" 32m;;
                   V)  PN[$sl]=varmail; VM_RUN=$((ps_ / 4)) VM_CHUNKS=4 phase_varmail $sl;;
                   F)  PN[$sl]=test4
                       # the 6 GiB file is written sequentially inside the phase (on the freed LBAs), then overwritten as before
                       HOT_IO=$((HOT_IO * ps_ / 600)) WARM_IO=$((WARM_IO * ps_ / 600)) COLD_IO=$((COLD_IO * ps_ / 600)) \
                         PRE_FIO=1 phase_fio $sl mix-test4.fio; ext $sl files "$FIO_TARGET";;
               esac; prev=$w
           done; A_NAME=${PN[A]}; B_NAME=${PN[B]};;
    mixT)  # 10-04 (user): app workloads in an irregular order, 9 phases x PH_SECS (default 4000 s) = 10 h:
           # YCSB-A -> OLTP -> Varmail -> YCSB-A -> YCSB-B -> FIO-Fast -> Varmail -> YCSB-A -> OLTP. Every phase is time-based:
           # YCSB via maxexecutiontime, filebench VM_RUN x 4 chunks (OLTP leak), FIO payload scaled from its 600 s x1 length.
           # Space: DB and OLTP files coexist next to the kept 6 GiB FIO file, so the same sizes as mixP (YCSB-A -> OLTP) are used:
           # 250k records and 32 MB OLTP files (mixP hit ENOSPC with 600k records + 64 MB files).
           ps_=${PH_SECS:-4000}; OPS=1000000000; RECORDS=250000; i=0; ld=1
           for w in YA O V YA YB F V YA O; do sl=$(printf "\\x$(printf %x $((65 + i)))"); i=$((i + 1))
               case $w in
                   YA) PN[$sl]=sqlite-a; YCSB_SECS=$ps_ phase_sqlite $sl a $ld; ld=0;;
                   YB) PN[$sl]=sqlite-b; YCSB_SECS=$ps_ phase_sqlite $sl b 0;;
                   O)  PN[$sl]=oltp; VM_RUN=$((ps_ / 4)) VM_CHUNKS=4 phase_filebench $sl oltp "" 32m;;
                   V)  PN[$sl]=varmail; VM_RUN=$((ps_ / 4)) VM_CHUNKS=4 phase_varmail $sl;;
                   F)  PN[$sl]=test4; HOT_IO=$((HOT_IO * ps_ / 600)) WARM_IO=$((WARM_IO * ps_ / 600)) COLD_IO=$((COLD_IO * ps_ / 600)) phase_fio $sl mix-test4.fio;;
               esac
           done; A_NAME=${PN[A]}; B_NAME=${PN[B]};;
    mixS)  # 10-04: ten phases cycling FIO-Fast -> Varmail -> OLTP (F V O F V O F V O F), each 10 min x MULT
           # (MULT=6 -> 1 h each, ~10 h). Filebench phases last VM_RUN x VM_CHUNKS (OLTP in chunks: memory leak).
           i=0; for w in F V O F V O F V O F; do sl=$(printf "\\x$(printf %x $((65 + i)))"); i=$((i + 1))
               case $w in F) PN[$sl]=test4; phase_fio $sl mix-test4.fio;; V) PN[$sl]=varmail; phase_varmail $sl;; O) PN[$sl]=oltp; phase_filebench $sl oltp "" 64m;; esac
           done; A_NAME=${PN[A]}; B_NAME=${PN[B]};;
    mixR)  A_NAME=test4; B_NAME=sqlite-a; C_NAME=test4; phase_fio A mix-test4.fio; phase_sqlite B; phase_fio C mix-test4.fio;;   # equal writes per phase so the phase-B optimum (arm17) matters in the total
    mixQ)  A_NAME=test4; B_NAME=idle-300s; C_NAME=test4; HOT_IO=$((HOT_IO/2)) WARM_IO=$((WARM_IO/2)) COLD_IO=$((COLD_IO/2)) phase_fio A mix-test4.fio; phase_idle B $(( ${SMOKE:+30} + ${SMOKE:-300} )); HOT_IO=$((HOT_IO/2)) WARM_IO=$((WARM_IO/2)) COLD_IO=$((COLD_IO/2)) phase_fio C mix-test4.fio;;  # idle gap between two identical phases
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
    for sl in C D E F G H I J; do [[ ! -f "$dir/phase-$sl-end.txt" ]] || printf 'phase%s(%s) %s\n' "$sl" "${PN[$sl]:-${C_NAME:-}}" "$(phase_waf "$dir/phase-$sl-start.txt" "$dir/phase-$sl-end.txt")"; done
    for sl in A B C; do [[ -f "$dir/phase-$sl-loaded.txt" ]] && printf 'phase%s-load %s\nphase%s-run %s\n' "$sl" "$(phase_waf "$dir/phase-$sl-start.txt" "$dir/phase-$sl-loaded.txt")" "$sl" "$(phase_waf "$dir/phase-$sl-loaded.txt" "$dir/phase-$sl-end.txt")"; done
    printf 'ycsb-load %s\nycsb-run %s\n' "$(grep -m1 'Throughput' "$dir/ycsb-load.txt")" "$(grep -m1 'Throughput' "$dir/ycsb-run.txt")"
} > "$dir/summary.txt"
cat "$dir/summary.txt"
gzip -f "$dir"/ycsb-run*.txt "$dir"/ycsb-load.txt 2>/dev/null || true   # YCSB per-second status is ~180 MB per 4M ops; GitHub caps files at 100 MB
