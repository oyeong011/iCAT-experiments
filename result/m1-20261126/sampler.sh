#!/usr/bin/env bash
# m1-20261126 resource sampler for one run: sampler.sh <out dir>. Read-only; never touches the device; no root
# (/proc/vmallocinfo needs root and is not in the sudo allow-list, so kernel memory is measured as /proc/meminfo deltas).
#  mem.tsv : 1 s samples for 60 s before nvmev loads (baseline), 1 s for the first 60 s after load (module allocations before mkfs/IO),
#            then every 60 s while loaded, then 60 s after unload. Columns: epoch, state, VmallocUsed kB, Slab kB, SUnreclaim kB, MemAvailable kB
#  stat.tsv: every 60 s while loaded, /proc/stat cpu, cpu1, cpu2 lines (emulator CPUs 1,2 utilisation check)
#  module.txt: /sys/module/nvmev/{coresize,initsize,taint} once after load
o=$1; mkdir -p "$o"
mem() { awk -v t="$(date +%s.%N)" -v s="$1" '/^VmallocUsed:/{v=$2}/^Slab:/{sl=$2}/^SUnreclaim:/{su=$2}/^MemAvailable:/{a=$2}END{printf "%s\t%s\t%s\t%s\t%s\t%s\n",t,s,v,sl,su,a}' /proc/meminfo >> "$o/mem.tsv"; }
printf 'epoch\tstate\tvmalloc_used_kb\tslab_kb\tsunreclaim_kb\tmemavail_kb\n' > "$o/mem.tsv"
ring=(); while [[ ! -e /sys/module/nvmev ]]; do ring+=("$(awk -v t="$(date +%s.%N)" '/^VmallocUsed:/{v=$2}/^Slab:/{sl=$2}/^SUnreclaim:/{su=$2}/^MemAvailable:/{a=$2}END{printf "%s\tpre\t%s\t%s\t%s\t%s",t,v,sl,su,a}' /proc/meminfo)"); ((${#ring[@]} > 60)) && ring=("${ring[@]:1}"); sleep 1; done
printf '%s\n' "${ring[@]}" >> "$o/mem.tsv"
for i in $(seq 60); do mem load1s; sleep 1; done
for f in coresize initsize taint; do echo "$f=$(cat /sys/module/nvmev/$f 2>/dev/null)"; done > "$o/module.txt"
while [[ -e /sys/module/nvmev ]]; do mem loaded; grep -E '^cpu[12]? ' /proc/stat | tr '\n' '|' | sed "s/^/$(date +%s)\t/" >> "$o/stat.tsv"; echo >> "$o/stat.tsv"; sleep 60; done
for i in $(seq 60); do mem post; sleep 1; done
