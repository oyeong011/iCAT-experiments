#!/usr/bin/env bash
# queue44 (10-06 15:20, DB also deleted before OLTP): mixV with the Table-3 prep (FIO file kept). Full-size short check first (PH_SECS=60, DB 600k: catches
# ENOSPC in phases 2/9 that SMOKE=1's tiny DB cannot), then iCAT-v4 10 h, then CAT-47 10 h. Launched with "hold=script/sqlite.sh".
cd /home/oy/iCAT; R=result/inherit-20261006; F=$R/fitcheck
push() { git add $R script/mix-inherit-20261006.sh script/gh-queue44-mixV.sh EXPERIMENT_LOG.md >/dev/null 2>&1; git commit -qm "mixV: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
fit_ok() { [[ $(cat $F/$1/exit-code.txt 2>/dev/null) == 0 && $(grep -c '^phase[A-I](' $F/$1/summary.txt 2>/dev/null) -ge 9 ]] && ! grep -qi 'no space left' $F/$1/*.txt $F/$1.console.txt 2>/dev/null; }
run() { local d=$1; shift; until [[ ! -e /sys/module/nvmev ]]; do sleep 5; done; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
  echo "start $d $(date -Is)"; "$@" || echo "FAIL $d"; }
mkdir -p $F
run fit-onlinev4 bash -c "env PH_SECS=60 MIX_BASE=$PWD/$F bash script/mix-inherit-20261006.sh mixV onlinev4 1 > $F/mixV-onlinev4-rep1.console.txt 2>&1"
fit_ok mixV-onlinev4-rep1 || { echo "FIT CHECK FAILED"; push "full-size short check FAILED"; sleep 86400; exit 1; }
push "full-size short check passed"
for p in onlinev4 fixed47; do
  run mixV-$p-rep1 bash -c "env PH_SECS=4000 bash script/mix-inherit-20261006.sh mixV $p 1 > $R/mixV-$p-rep1.console.txt 2>&1"; push "10h $p"
done
echo QUEUE43DONE $(date -Is)
