#!/usr/bin/env bash
# 11-22 resume after smartgc rep1 hit a full disk (chmodel log flood; rsyslog now drops that line,
# /etc/rsyslog.d/10-nvmev-chmodel-flood.conf). Runs smartgc, smartgcq-eq8, onlinev4 with rep 1 (same seeds as the
# other runs) into result/smartgc-20261119/resume/ via MIX_BASE, so no existing directory is touched.
# ponytail: a failed run is logged and the queue goes on (user: do not stop).
cd /home/oy/iCAT; S=$PWD/result/smartgc-20261119; B=$S/resume; mkdir -p $B
SEQ="F S V F V S F S V F V S F S V F V S F S"
snap() { # same as smartgc-queue-20261119.sh
  local th="" pid
  for pid in $(ps -eo pid=,comm= | awk '$2 ~ /^nvmev/ {print $1}'); do
    th+="$pid:$(cat /proc/$pid/comm):$(cut -d' ' -f1 /proc/$pid/schedstat 2>/dev/null):$(awk '{print $14":"$15}' /proc/$pid/stat 2>/dev/null):rss=$(grep -m1 VmRSS /proc/$pid/status 2>/dev/null | awk '{print $2}' || true);"
  done
  printf '%s tag=%s %s coresize=%s threads="%s"\n' "$(date +%s.%N)" "$2" \
    "$(awk '/^(MemTotal|MemAvailable|VmallocUsed|Slab|SUnreclaim|Percpu|KernelStack):/{printf "%s=%s ",$1,$2}' /proc/meminfo | tr -d :)" \
    "$(cat /sys/module/nvmev/coresize 2>/dev/null || echo NA)" "$th" >> $1; }
for p in smartgc smartgcq-eq8 onlinev4; do
  D=$B/mixY-$p-rep1
  [[ -e $D ]] && { echo "SKIP $p: $D exists"; continue; }
  until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done
  mod=buildoutput/nvmev-$p.ko; [[ $p == onlinev4 ]] && mod=buildoutput/nvmev-online-v4.ko
  M=$B/$p-rep1.samples.txt; : > $M; snap $M before
  git rev-parse HEAD > $B/$p-rep1.commit.txt; sha256sum $mod > $B/$p-rep1.module.sha256
  printf 'policy=%s module=%s MIXY_SEQ="%s" PH_SECS=1800 MIX_BASE=%s sampler=30s\n' $p $mod "$SEQ" $B > $B/$p-rep1.config.txt
  echo "start $p $(date -Is) disk_free=$(df --output=avail -h / | tail -1)"
  env MIXY_SEQ="$SEQ" PH_SECS=1800 MIX_BASE=$B bash script/mix-gc-20261010.sh mixY $p 1 > $B/mixY-$p-rep1.console.txt 2>&1 &
  run=$!
  while kill -0 $run 2>/dev/null; do [[ -e /sys/module/nvmev ]] && snap $M run; sleep 30; done
  snap $M after
  wait $run && echo "[done] $p $(date -Is)" || echo "FAIL $p $(date -Is) - continuing"
  git add $B EXPERIMENT_LOG.md >/dev/null 2>&1
  git commit -qm "smartgc-20261119 resume: mixY $p rep1" >/dev/null 2>&1; git push -q 2>/dev/null
done
echo RESUMEDONE $(date -Is)
