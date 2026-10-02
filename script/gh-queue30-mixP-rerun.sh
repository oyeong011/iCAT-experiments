#!/usr/bin/env bash
# 2026-09-30: re-run mixP arm46/fixed37 x3 (failed 02:25/03:08 with a corrupted loader/library copy in memory, second such incident).
set -u
cd /home/oy/iCAT
until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done
for p in arm46 fixed37; do d=result/mix-20260911/mixP-$p-rep1-x3
  [[ -e $d/summary.txt ]] && continue; rm -rf $d; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null
  fio --version >/dev/null 2>&1 && sqlite3 --version >/dev/null 2>&1 && java -version >/dev/null 2>&1 || { echo "tools broken before $p"; continue; }
  MULT=3 VM_RUN=900 bash script/mix-20260911.sh mixP $p 1 > $d.console.txt 2>&1 || echo "FAIL $d"
done
python3 analysis/all-tables.py > /dev/null 2>&1; python3 analysis/figures.py > /dev/null 2>&1
git add -A >/dev/null 2>&1; git commit -qm "mixP arm46/fixed37 rerun; tables and figures regenerated" >/dev/null 2>&1; git push -q 2>/dev/null
echo QUEUE30DONE $(date -Is)
