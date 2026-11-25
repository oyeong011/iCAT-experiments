#!/usr/bin/env bash
# abl-20261125 (copied from revD-20261124 run-one.sh; paths only). usage: run-one.sh <policy> <rep> [smoke]
# (copy of GoCom revC run-one.sh; paths only)
set -u
C=/home/oy/iCAT/result/revision-additional-ablation
pol=$1; rep=$2; smoke=${3:-}
ph=1800; [[ -z "$smoke" ]] || ph=120
tag="mixFYF-$pol-rep$rep${smoke:+-smoke120}"
exec 8>>/home/oy/iCAT/result/mix-20260911/device.lock
flock -n 8 || { echo "device lock busy" >&2; exit 75; }
cd /home/oy/iCAT
env PH_SECS=$ph REVA_SMOKE=${smoke:+1} ICAT_SEED=$((2026111400 + rep)) MIX_BASE=$C/raw MIX_JOURNAL=$C/journal.md \
    BASH_ENV=$C/safety-env.sh MIXX_LOCK_HELD=1 \
    bash $C/runner-abl.sh mixFYF "$pol" "$rep" > $C/console/$tag.console.txt 2>&1
rc=$?
printf '%s\t%s\t%s\t%s\n' "$(date -Is)" "$tag" "$rc" "$C/raw/$tag" >> $C/runs.tsv
exit $rc
