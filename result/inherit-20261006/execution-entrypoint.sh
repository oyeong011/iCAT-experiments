#!/usr/bin/env bash
set -Eeuo pipefail
cd /home/oy/iCAT
for p in fixed37 fixed50; do
  printf '%s\n' "$p-long" > /home/oy/iCAT/result/inherit-20261006/current-stage.txt
  env MIXV_FIO_GB=5 MIXV_RECORDS=600000 PH_SECS=4000 bash /home/oy/iCAT/result/inherit-20261006/execution-mix.sh mixV "$p" 1
  python3 /home/oy/iCAT/result/inherit-20261006/stage-finished.py "$p" long
done
