#!/usr/bin/env bash
# 11-23 revision E1+E2 (report/revision-20261123/additional_experiment_plan.md): after E0 (fixed47 mixY F S V F) ends,
# smoke v4nodrift, then mixR x3 interleaved v4 / v4nodrift / v4fullreset for rep 1..3, then fixed47 rep 1.
# 11-23 23:40 (user, after GoCom duplication check): random45 dropped; revA-Random (GoCom, mixFYF n=3) is used instead.
# All output under result/revision-20261123/mixR (MIX_BASE); a failed run is logged and the queue goes on.
cd /home/oy/iCAT; B=$PWD/result/revision-20261123/mixR; mkdir -p $B
E0=result/revision-20261123/check-fixed47-nov/mixY-fixed47-rep1
until [[ -f $E0/exit-code.txt && ! -e /sys/module/nvmev ]]; do sleep 60; done
echo "E0 exit=$(cat $E0/exit-code.txt) $(date -Is)"
run() { # run <policy> <rep> [SMOKE]
  echo "start $1 rep$2 ${3:+smoke} $(date -Is) disk=$(df --output=avail -h / | tail -1)"
  sha256sum buildoutput/nvmev-$( [[ $1 == fixed47 ]] && echo varmail-20260908-fixed47 || echo online-${1#online}).ko > $B/$1-rep$2${3:+-smoke}.module.sha256 2>/dev/null
  git rev-parse HEAD > $B/$1-rep$2${3:+-smoke}.commit.txt
  env MIX_BASE=$B MULT=3 ${3:+SMOKE=1} bash script/mix-20260911.sh mixR $1 $2 > $B/mixR-$1-rep$2${3:+-smoke}.console.txt 2>&1 \
    && echo "[done] $1 rep$2 $(date -Is)" || echo "FAIL $1 rep$2 $(date -Is) - continuing"
  until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done
  git add $B EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "revision-20261123: mixR $1 rep$2${3:+ smoke}" >/dev/null 2>&1; git push -q 2>/dev/null; }
run onlinev4nodrift 1 smoke
for p in onlinev4nodrift; do  # smoke check: tuner lines present
  k=$B/mixR-$p-rep1-x3-smoke/kernel.log; n=$(grep -c 'WATGC_V2 sample' $k 2>/dev/null); a=$(grep -o 'evaluated=[0-9]*' $k 2>/dev/null | sort -u | wc -l)
  echo "smoke $p samples=$n distinct_arms=$a"; (( n > 0 )) || { echo "FAIL smoke $p - stopping"; exit 1; }; done
for r in 1 2 3; do for p in onlinev4 onlinev4nodrift onlinev4fullreset; do run $p $r; done; done
run fixed47 1
echo REVISIONQUEUEDONE $(date -Is)
