#!/usr/bin/env bash
# 11-14 resource overhead: Fixed CAT-47 vs iCAT v1/v2/v4 (instrumented, -DRES_INSTR), FIO-Fast 1800 s after mixY prep,
# 3 reps in a balanced order, then one uninstrumented run each for the WAF check. No sudo beyond the existing sudoers.
# Samples every 10 s: /proc/meminfo, /sys/module/nvmev/coresize, nvmev kthreads (schedstat ns, stat utime/stime, status VmRSS).
cd /home/oy/iCAT; B=$PWD/result/resource-v124-20261114; mkdir -p $B
git rev-parse HEAD > $B/start-commit.txt
snap() { # snap <file> <tag>
  local th="" pid
  for pid in $(ps -eo pid=,comm= | awk '$2 ~ /^nvmev/ {print $1}'); do
    th+="$pid:$(cat /proc/$pid/comm):$(cut -d' ' -f1 /proc/$pid/schedstat 2>/dev/null):$(awk '{print $14":"$15}' /proc/$pid/stat 2>/dev/null):rss=$(grep -m1 VmRSS /proc/$pid/status 2>/dev/null | awk '{print $2}' || true);"
  done
  printf '%s tag=%s %s coresize=%s threads="%s"\n' "$(date +%s.%N)" "$2" \
    "$(awk '/^(MemTotal|MemAvailable|VmallocUsed|Slab|SUnreclaim|Percpu|KernelStack):/{printf "%s=%s ",$1,$2}' /proc/meminfo | tr -d :)" \
    "$(cat /sys/module/nvmev/coresize 2>/dev/null || echo NA)" "$th" >> $1; }
one() { # one <policy> <rep>
  local p=$1 rep=$2 D=$B/mixY-$1-rep$2 M=$B/$1-rep$2.samples.txt run loaded=0
  [[ -f $D/summary.txt ]] && return
  until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
  : > $M; snap $M before; echo "start $p rep$rep $(date -Is)"
  env MIXY_SEQ="F" PH_SECS=1800 MIX_BASE=$B bash script/mix-gc-20261010.sh mixY $p $rep > $B/$p-rep$rep.console.txt 2>&1 &
  run=$!
  while kill -0 $run 2>/dev/null; do
    if [[ -e /sys/module/nvmev ]]; then (( loaded )) || { snap $M loaded; loaded=1; }; snap $M run; fi
    sleep 10
  done
  snap $M after
  if ! wait $run; then echo "FAIL $p rep$rep $(date -Is) - stopping (rule 6)"; exit 1; fi
  grep -h 'RESOURCE' $D/kernel.log 2>/dev/null | sed 's/^\[[^]]*\] //' | sort -u > $B/$p-rep$rep.resource.txt
  git add $B script/resource-v124-20261114.sh script/mix-gc-20261010.sh EXPERIMENT_LOG.md >/dev/null 2>&1
  git commit -qm "resource-v124: $p rep$rep" >/dev/null 2>&1; git push -q -u origin resource-overhead-20261114 2>/dev/null; echo "[push] $p rep$rep $(date -Is)"
}
for p in resfixed47 resv1 resv2 resv4; do one $p 1; done
for p in resv4 resv2 resv1 resfixed47; do one $p 2; done
for p in resv2 resfixed47 resv4 resv1; do one $p 3; done
for p in resfixed47n online onlinev2 onlinev4; do one $p 1; done   # WAF check, uninstrumented
echo RESOURCEDONE $(date -Is)
