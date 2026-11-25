#!/usr/bin/env bash
# m1-20261126 userspace CPU benchmark (device-free). Real conv_ftl.c of the two instrumented trees driven by sim/sim.c
# (fake clock, zero-delay channel; its WAF is NOT a measurement). Pinned to CPU 11 (SMT sibling 5 idle), normal priority,
# run only when no kernel experiment is active. Modes: M1PROF_CPU=1 thread CPU time (~1 us per clock read),
# M1PROF_CPU=2 CLOCK_MONOTONIC on the pinned single-thread process (~40 ns per region); 3 seeds each.
set -u; cd "$(dirname "$0")"; mkdir -p sim/bench
for seed in 1 2 3; do for pol in icat smartgc-eq8; do for mode in 2 1; do
  t=$([ $pol = icat ] && echo icat || echo smartgc); x=$([ $pol = icat ] || echo "seed=$seed")
  f=sim/bench/$pol-m$mode-s$seed.log; [[ -e $f ]] && continue
  { echo "# $(date -Is) host=$(hostname) pol=$pol mode=$mode seed=$seed src=m1-$t-src sha=$(sha256sum m1-$t-src/conv_ftl.c | cut -c1-16) cpu=$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2)"
    SIM_SRC=m1-$t-src SIM_CFLAGS=-DM1PROF_CPU=$mode SIM_OUT=$(mktemp -d) /usr/bin/time -f 'm1time wall_s=%e user_s=%U sys_s=%S' \
      taskset -c 11 bash sim/run.sh $pol capacity_mib=8192 overwrite_x=6 workload=zones sim_seed=$seed $x 2>&1; echo "exit=$?"; } > $f
done; done; done
grep -L 'invariants=ok' sim/bench/*.log && echo "SIM FAIL" || echo "SIM OK"
