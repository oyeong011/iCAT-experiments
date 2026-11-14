#!/usr/bin/env bash
# Userspace FTL-driver runs of smartgc-dev-20261114 (see EXPERIMENT_LOG.md). Run inside WSL/Linux from the repo root:
#   bash result/smartgc-dev-20261114/run-sims.sh <stage1|stage2|stage3>
# One log per run in this directory; an existing log is never overwritten.
set -u
d=result/smartgc-dev-20261114
tmp=${SIM_TMP:-$HOME/sgbuild/sim-runs}
run() { # run <name> <module source dir> <policy> [sim options]
    local name=$1 src=$2 policy=$3; shift 3
    [[ ! -e "$d/$name.log" ]] || { echo "skip $name (log exists)"; return; }
    (
        export SIM_SRC=$src SIM_OUT=$tmp/$name
        { echo "# started $(date -Is) SIM_SRC=$src policy=$policy options: $*"
          bash smartgc-src/test/run.sh "$policy" "$@"; echo "exit=$?"; echo "# finished $(date -Is)"; } > "$d/$name.log" 2>&1
    ) &
}
X="capacity_mib=8192 overwrite_x=6"
case ${1:?stage} in
stage1) # correctness of SmartGC paths + unchanged Greedy / fixed CAT behaviour
    run s1-smartgc-default      smartgc-src         smartgc $X
    run s1-smartgc-gcbuf0       smartgc-src         smartgc $X gcbuf=0
    run s1-smartgc-gcbuf50      smartgc-src         smartgc $X gcbuf=50
    run s1-smartgc-batch1       smartgc-src         smartgc $X batch=1
    run s1-smartgc-batch64      smartgc-src         smartgc $X batch=64
    run s1-smartgc-uniform      smartgc-src         smartgc $X workload=uniform
    run s1-greedy-new           smartgc-src         greedy  $X
    run s1-greedy-old           varmail-compare-src greedy  $X
    run s1-arm47-new            smartgc-src         arm47   $X
    run s1-arm47-old            varmail-compare-src arm47   $X
    run s1-greedy-uniform-new   smartgc-src         greedy  $X workload=uniform
    ;;
stage2) # reward weight w and discount factor: not given in the paper
    for w in 10000 100000; do for g in 900 500 0; do
        run s2-smartgc-w$w-g$g smartgc-src smartgc $X gcbuf=0 w=$w gamma=$g
    done; done
    run s2-smartgc-w1000-g500 smartgc-src smartgc $X gcbuf=0 gamma=500
    run s2-smartgc-w1000-g0   smartgc-src smartgc $X gcbuf=0 gamma=0
    ;;
stage3) # added after stage2: is the gap to Greedy the zero-initialised Q-table (never-erased states rank last)?
    run s3-smartgc-qinit2000              smartgc-src smartgc $X q_init=2000
    run s3-smartgc-qinit2000-gcbuf0       smartgc-src smartgc $X q_init=2000 gcbuf=0
    run s3-smartgc-qinit2000-gcbuf0-g0    smartgc-src smartgc $X q_init=2000 gcbuf=0 gamma=0
    run s3-smartgc-qinit2000-gcbuf0-eps0  smartgc-src smartgc $X q_init=2000 gcbuf=0 eps_start=0 eps_min=0
    run s3-smartgc-qinit2000-gcbuf0-g0-eps0 smartgc-src smartgc $X q_init=2000 gcbuf=0 gamma=0 eps_start=0 eps_min=0
    run s3-smartgc-qinit2000-batch1       smartgc-src smartgc $X q_init=2000 batch=1
    run s3-smartgc-qinit2000-uniform      smartgc-src smartgc $X q_init=2000 workload=uniform
    run s3-smartgc-eps300const-gcbuf0     smartgc-src smartgc $X gcbuf=0 eps_min=300
    ;;
stage4) # added after stage3: after the next-state fix (erased line -> empty line); repeats the informative stage1-3 cases
    run s4-smartgc-default                smartgc-src smartgc $X
    run s4-smartgc-gcbuf0                 smartgc-src smartgc $X gcbuf=0
    run s4-smartgc-gcbuf50                smartgc-src smartgc $X gcbuf=50
    run s4-smartgc-batch1                 smartgc-src smartgc $X batch=1
    run s4-smartgc-batch64                smartgc-src smartgc $X batch=64
    run s4-smartgc-uniform                smartgc-src smartgc $X workload=uniform
    run s4-smartgc-gcbuf0-g0              smartgc-src smartgc $X gcbuf=0 gamma=0
    run s4-smartgc-eps300const-gcbuf0     smartgc-src smartgc $X gcbuf=0 eps_min=300
    run s4-smartgc-qinit2000              smartgc-src smartgc $X q_init=2000
    run s4-smartgc-qinit2000-gcbuf0       smartgc-src smartgc $X q_init=2000 gcbuf=0
    run s4-smartgc-qinit2000-gcbuf50      smartgc-src smartgc $X q_init=2000 gcbuf=50
    run s4-smartgc-qinit2000-gcbuf0-g0    smartgc-src smartgc $X q_init=2000 gcbuf=0 gamma=0
    run s4-smartgc-qinit2000-batch1       smartgc-src smartgc $X q_init=2000 batch=1
    run s4-smartgc-qinit2000-batch64      smartgc-src smartgc $X q_init=2000 batch=64
    run s4-smartgc-qinit2000-uniform      smartgc-src smartgc $X q_init=2000 workload=uniform
    run s4-smartgc-qinit2000-w10000       smartgc-src smartgc $X q_init=20000 w=10000
    run s4-greedy-new                     smartgc-src greedy  $X
    run s4-arm47-new                      smartgc-src arm47   $X
    ;;
*) echo "unknown stage $1" >&2; exit 2;;
esac
wait
grep -H "^sim \|^exit=\|BUG\|INVARIANT" "$d"/s${1#stage}-*.log
