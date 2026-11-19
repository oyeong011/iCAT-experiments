#!/usr/bin/env bash
# 11-19 SmartGC comparison queue (SMARTGC_RUN_GUIDE.md §4, computer-B brief §6): after the running smartgc-eq8,
# run sg-arm47 → smartgc → smartgcq-eq8, one at a time, mixY 20 phases × 1800 s. Stops on the first failure.
# Samples every 30 s into result/smartgc-20261119/: /proc/meminfo, nvmev coresize, nvmev kthreads (schedstat ns, utime:stime, VmRSS).
# usage: script/smartgc-queue-20261119.sh            (queue)
#        script/smartgc-queue-20261119.sh attach <p> (sample an already-running policy until its exit-code.txt appears)
cd /home/oy/iCAT; S=$PWD/result/smartgc-20261119; R=$PWD/result/gc-20261010; mkdir -p $S
SEQ="F S V F V S F S V F V S F S V F V S F S"
snap() { # snap <file> <tag>
  local th="" pid
  for pid in $(ps -eo pid=,comm= | awk '$2 ~ /^nvmev/ {print $1}'); do
    th+="$pid:$(cat /proc/$pid/comm):$(cut -d' ' -f1 /proc/$pid/schedstat 2>/dev/null):$(awk '{print $14":"$15}' /proc/$pid/stat 2>/dev/null):rss=$(grep -m1 VmRSS /proc/$pid/status 2>/dev/null | awk '{print $2}' || true);"
  done
  printf '%s tag=%s %s coresize=%s threads="%s"\n' "$(date +%s.%N)" "$2" \
    "$(awk '/^(MemTotal|MemAvailable|VmallocUsed|Slab|SUnreclaim|Percpu|KernelStack):/{printf "%s=%s ",$1,$2}' /proc/meminfo | tr -d :)" \
    "$(cat /sys/module/nvmev/coresize 2>/dev/null || echo NA)" "$th" >> $1; }
sample_until_done() { # <policy>: sample while the run is going, then once after
  local M=$S/$1-rep1.samples.txt D=$R/mixY-$1-rep1
  until [[ -f $D/exit-code.txt ]]; do [[ -e /sys/module/nvmev ]] && snap $M run; sleep 30; done
  snap $M after; }
if [[ $1 == attach ]]; then sample_until_done $2; exit; fi

# wait for the running smartgc-eq8 to finish and release the device
until [[ -f $R/mixY-smartgc-eq8-rep1/exit-code.txt && ! -e /sys/module/nvmev ]]; do sleep 60; done
[[ $(cat $R/mixY-smartgc-eq8-rep1/exit-code.txt) == 0 ]] || { echo "FAIL smartgc-eq8 exit=$(cat $R/mixY-smartgc-eq8-rep1/exit-code.txt) $(date -Is) - queue not started"; exit 1; }
git add $S $R/mixY-smartgc-eq8-rep1 $R/mixY-smartgc-eq8-rep1.console.txt EXPERIMENT_LOG.md >/dev/null 2>&1
git commit -qm "smartgc-20261119: mixY smartgc-eq8 rep1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] smartgc-eq8 $(date -Is)"
for p in sg-arm47 smartgc smartgcq-eq8; do
  D=$R/mixY-$p-rep1
  [[ -e $D ]] && { echo "SKIP $p: $D exists (not overwriting)"; continue; }
  until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done
  M=$S/$p-rep1.samples.txt; : > $M; snap $M before
  echo "start $p $(date -Is) expected_end $(date -d '+10 hours 15 minutes' -Is)"
  git rev-parse HEAD > $S/$p-rep1.commit.txt; sha256sum buildoutput/nvmev-$p.ko > $S/$p-rep1.module.sha256
  env MIXY_SEQ="$SEQ" PH_SECS=1800 bash script/mix-gc-20261010.sh mixY $p 1 > $R/mixY-$p-rep1.console.txt 2>&1 &
  run=$!
  while kill -0 $run 2>/dev/null; do [[ -e /sys/module/nvmev ]] && snap $M run; sleep 30; done
  snap $M after
  if ! wait $run; then echo "FAIL $p $(date -Is) - stopping"; exit 1; fi
  git add $S $D $R/mixY-$p-rep1.console.txt EXPERIMENT_LOG.md >/dev/null 2>&1
  git commit -qm "smartgc-20261119: mixY $p rep1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $p $(date -Is)"
done
echo SMARTGCQUEUEDONE $(date -Is)
