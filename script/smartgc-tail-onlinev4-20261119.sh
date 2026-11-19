#!/usr/bin/env bash
# 11-19 follow-up to script/smartgc-queue-20261119.sh (left untouched while it runs): after that queue prints
# SMARTGCQUEUEDONE, run iCAT V4 (onlinev4) once with the same mixY SEQ / PH_SECS=1800 and the same 30 s sampler.
# Output goes to result/smartgc-20261119/mixY-onlinev4-rep1 (MIX_BASE), never over an existing directory.
cd /home/oy/iCAT; S=$PWD/result/smartgc-20261119; p=onlinev4; D=$S/mixY-$p-rep1; M=$S/$p-rep1.samples.txt
SEQ="F S V F V S F S V F V S F S V F V S F S"
snap() { # same as smartgc-queue-20261119.sh
  local th="" pid
  for pid in $(ps -eo pid=,comm= | awk '$2 ~ /^nvmev/ {print $1}'); do
    th+="$pid:$(cat /proc/$pid/comm):$(cut -d' ' -f1 /proc/$pid/schedstat 2>/dev/null):$(awk '{print $14":"$15}' /proc/$pid/stat 2>/dev/null):rss=$(grep -m1 VmRSS /proc/$pid/status 2>/dev/null | awk '{print $2}' || true);"
  done
  printf '%s tag=%s %s coresize=%s threads="%s"\n' "$(date +%s.%N)" "$2" \
    "$(awk '/^(MemTotal|MemAvailable|VmallocUsed|Slab|SUnreclaim|Percpu|KernelStack):/{printf "%s=%s ",$1,$2}' /proc/meminfo | tr -d :)" \
    "$(cat /sys/module/nvmev/coresize 2>/dev/null || echo NA)" "$th" >> $1; }
until grep -q 'SMARTGCQUEUEDONE\|FAIL' $S/queue.out 2>/dev/null; do sleep 60; done
grep -q FAIL $S/queue.out && { echo "queue reported FAIL - onlinev4 not started $(date -Is)"; exit 1; }
[[ -e $D ]] && { echo "SKIP $p: $D exists"; exit 0; }
until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done
mod=buildoutput/nvmev-online-v4.ko
[[ $(sha256sum < $mod | cut -c1-64) == db93f822a2e79f1e9ae492ac733e783df175604814d6985641fae913f8f8eda4 ]] || { echo "FAIL $mod sha256 changed - not started"; exit 1; }
git rev-parse HEAD > $S/$p-rep1.commit.txt; sha256sum $mod > $S/$p-rep1.module.sha256
printf 'policy=%s module=%s MIXY_SEQ="%s" PH_SECS=1800 MIX_BASE=%s sampler=30s\n' $p $mod "$SEQ" $S > $S/$p-rep1.config.txt
: > $M; snap $M before; echo "start $p $(date -Is) expected_end $(date -d '+10 hours 15 minutes' -Is)"
env MIXY_SEQ="$SEQ" PH_SECS=1800 MIX_BASE=$S bash script/mix-gc-20261010.sh mixY $p 1 > $S/mixY-$p-rep1.console.txt 2>&1 &
run=$!
while kill -0 $run 2>/dev/null; do [[ -e /sys/module/nvmev ]] && snap $M run; sleep 30; done
snap $M after
if ! wait $run; then echo "FAIL $p $(date -Is)"; exit 1; fi
git add $S EXPERIMENT_LOG.md >/dev/null 2>&1
git commit -qm "smartgc-20261119: mixY onlinev4 rep1 (iCAT V4 baseline)" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $p $(date -Is)"
echo ONLINEV4DONE $(date -Is)
