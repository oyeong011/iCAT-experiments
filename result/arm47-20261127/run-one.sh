#!/usr/bin/env bash
# arm47-20261127 (copy of batchG-20261126 run-one.sh; paths only). usage: run-one.sh <policy> <rep> [smoke]
set -u
C=/home/oy/iCAT/result/arm47-20261127
pol=$1; rep=$2; smoke=${3:-}
case $pol in arm47) R=$C/raw;; *) exit 2;; esac
ph=1800; [[ -z "$smoke" ]] || ph=120
tag="mixFYF-$pol-rep$rep${smoke:+-smoke120}"
exec 8>>/home/oy/iCAT/result/mix-20260911/device.lock
flock -n 8 || { echo "device lock busy" >&2; exit 75; }
cd /home/oy/iCAT
env PH_SECS=$ph REVA_SMOKE=${smoke:+1} ICAT_SEED=$((2026111400 + rep)) MIX_BASE=$R MIX_JOURNAL=$C/journal.md \
    BASH_ENV=$C/safety-env.sh MIXX_LOCK_HELD=1 \
    bash $C/runner-arm47.sh mixFYF "$pol" "$rep" > $C/console/$tag.console.txt 2>&1
rc=$?
printf '%s\t%s\t%s\t%s\n' "$(date -Is)" "$tag" "$rc" "$R/$tag" >> $C/runs.tsv
exit $rc
