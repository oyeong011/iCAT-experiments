#!/usr/bin/env bash
# 2026-10-02, second machine: rank ALL 60 fixed CAT arms on every transition workload.
# Stage 1: every arm00..arm59 at x1 on 11 mixes (mixA/mixC already complete on the original machine).
# Stage 2: per mix, the top-5 fixed arms over all 60 at x3 (MULT=3, VM_RUN=900) unless already there.
# Pushes to branch icat-2 only (the original machine merges it), so the two machines never race on main.
# Results go to result/icat2-fullsweep (never into the original machine's result/mix-20260911) and the per-run
# journal to EXPERIMENT_LOG-icat2.md, so nothing the original machine wrote is skipped, deleted or merged over.
# Each run dir gets HOST.txt.
set -u
cd ~/iCAT
export MIX_BASE=$HOME/iCAT/result/icat2-fullsweep MIX_JOURNAL=$HOME/iCAT/EXPERIMENT_LOG-icat2.md; mkdir -p $MIX_BASE
free() { until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done; }
tools() { fio --version >/dev/null 2>&1 && sqlite3 --version >/dev/null 2>&1 && java -version >/dev/null 2>&1; }
push() { git add result/icat2-fullsweep EXPERIMENT_LOG-icat2.md >/dev/null 2>&1; git commit -qm "fullsweep($(hostname)): $1" >/dev/null 2>&1; git push -q origin HEAD:icat-2 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/icat2-fullsweep
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; free
  if [[ -d $R/$d ]]; then t=$(date +%Y%m%d%H%M%S); mv $R/$d $R/$d-failed-$t; mv $R/$d.console.txt $R/$d-failed-$t.console.txt 2>/dev/null; fi   # keep failed attempts
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; tools || { echo "tools broken before $d, skipped"; return; }
  "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"
  mkdir -p $R/$d; hostname > $R/$d/HOST.txt
  tools || { echo "SUSPECT $d: tools broken right after this run" | tee -a $R/$d/SUSPECT.txt; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; }; }
MIXES="mixO mixF mixJ mixP mixB mixD mixK mixH mixG mixL mixQ"
for lb in $MIXES; do for i in $(seq -w 0 59); do run $lb-arm$i-rep1 bash script/mix-20260911.sh $lb arm$i 1; done; push "$lb all 60 arms (x1)"; done
echo SWEEPDONE $(date -Is)
for lb in $MIXES; do
  top=$(python3 - $lb <<'PY'
import re, sys
from pathlib import Path
M = Path.home() / 'iCAT/result/icat2-fullsweep'; lb = sys.argv[1]; w = {}
for d in M.glob(f'{lb}-arm[0-9][0-9]-rep1'):
    f = d / 'summary.txt'
    if not f.exists() or (d / 'SUSPECT.txt').exists(): continue
    m = re.search(r'^total .*WAF=([\d.]+)', f.read_text(), re.M)
    if m: w[d.name.split('-')[1]] = float(m[1])
print(' '.join(sorted(w, key=w.get)[:5]))
PY
)
  echo "$lb top5 at x1: $top"
  for p in $top; do run $lb-$p-rep1-x3 env MULT=3 VM_RUN=900 bash script/mix-20260911.sh $lb $p 1; done; push "$lb top5 confirmed (x3): $top"
done
echo QUEUE33DONE $(date -Is)
