#!/usr/bin/env bash
# revE-20261125: every 30 s -> loadsampler.tsv: time, load1/5/15, CPU1 and CPU2 busy % (from /proc/stat deltas), all-CPU busy %, current queue entry.
C=/home/oy/iCAT/result/revE-20261125; O=$C/loadsampler.tsv
[[ -s $O ]] || printf 'time\tload1\tload5\tload15\tcpu1_busy_pct\tcpu2_busy_pct\tall_busy_pct\tnvmev_loaded\tqueue_entry\n' > $O
echo $$ > $C/loadsampler.pid
read_cpu() { awk -v c="$1" '$1==c{idle=$5+$6; t=0; for(i=2;i<=NF;i++) t+=$i; print t, idle}' /proc/stat; }
read -r t1a i1a < <(read_cpu cpu1); read -r t2a i2a < <(read_cpu cpu2); read -r ta ia < <(read_cpu cpu)
while true; do
  sleep 30
  read -r t1b i1b < <(read_cpu cpu1); read -r t2b i2b < <(read_cpu cpu2); read -r tb ib < <(read_cpu cpu)
  b1=$(awk -v t=$((t1b-t1a)) -v i=$((i1b-i1a)) 'BEGIN{printf "%.1f", t?100*(t-i)/t:0}')
  b2=$(awk -v t=$((t2b-t2a)) -v i=$((i2b-i2a)) 'BEGIN{printf "%.1f", t?100*(t-i)/t:0}')
  ba=$(awk -v t=$((tb-ta)) -v i=$((ib-ia)) 'BEGIN{printf "%.1f", t?100*(t-i)/t:0}')
  t1a=$t1b; i1a=$i1b; t2a=$t2b; i2a=$i2b; ta=$tb; ia=$ib
  entry=$(grep -E ' start ' $C/queue.log $C/queue-main.log 2>/dev/null | tail -1 | sed 's/.* start //')
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -Is)" "$(cut -d' ' -f1-3 /proc/loadavg | tr ' ' '\t')" "$b1" "$b2" "$ba" "$([[ -e /sys/module/nvmev ]] && echo 1 || echo 0)	$entry" >> $O
done
