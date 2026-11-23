#!/usr/bin/env bash
# revA read-only memory sampler (added 2026-11-14 20:5x during arm47 rep1): no device operations.
out=/home/oy/iCAT/result/revA-20261114/memsampler.tsv
[[ -s $out ]] || printf 'epoch\tnvmev_loaded\tcoresize_B\tMemAvailable_kB\tSlab_kB\tSUnreclaim_kB\tVmallocUsed_kB\tPercpu_kB\tdispatcher_rss_kB\n' > $out
while pgrep -f revA-20261114/queue.sh >/dev/null; do
  m() { awk -v k="$1:" '$1==k{print $2}' /proc/meminfo; }
  l=0; c=; [[ -e /sys/module/nvmev ]] && { l=1; c=$(cat /sys/module/nvmev/coresize); }
  r=$(ps -C nvmev_dispatche -o rss= 2>/dev/null | head -1 | tr -d ' ')
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' $(date +%s) $l "$c" $(m MemAvailable) $(m Slab) $(m SUnreclaim) $(m VmallocUsed) $(m Percpu) "$r" >> $out
  sleep 60
done
