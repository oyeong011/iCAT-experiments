#!/usr/bin/env bash
# 2026-09-30: which fixed arm is really best / robust on the transition workloads?
# Stage 1 (screen): 13 candidate arms at x1 on 11 mixes (mixA/mixC already have all 60 at x1; 37/47/50 already have x1).
# Stage 2 (confirm): per mix, the top-3 fixed arms by x1 WAF are run at x3 (MULT=3, VM_RUN=900) unless already there.
# After every run: drop caches + check fio/sqlite3/java; if broken right after a run, mark that run SUSPECT.
set -u
cd /home/oy/iCAT
S=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
until grep -q QUEUE30DONE $S/queue30.out 2>/dev/null; do sleep 120; done
free() { until ! pgrep -f "script/(mix-20260911|gh-fio|sqlite|gh-filebench).sh" >/dev/null && [[ ! -e /sys/module/nvmev ]]; do sleep 30; done; }
tools() { fio --version >/dev/null 2>&1 && sqlite3 --version >/dev/null 2>&1 && java -version >/dev/null 2>&1; }
push() { git add -A >/dev/null 2>&1; git commit -qm "screen/confirm: $1" >/dev/null 2>&1; git push -q 2>/dev/null; echo "[push] $1 $(date -Is)"; }
R=result/mix-20260911
run() { local d=$1; shift; [[ -e $R/$d/summary.txt ]] && return; free; rm -rf $R/$d
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; tools || { echo "tools broken before $d, skipped"; return; }
  "$@" > $R/$d.console.txt 2>&1 || echo "FAIL $d"
  tools || { echo "SUSPECT $d: tools broken right after this run" | tee -a $R/$d/SUSPECT.txt; echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null; }; }
MIXES="mixO mixF mixJ mixP mixB mixD mixK mixH mixG mixL mixQ"
ARMS="46 31 32 17 16 15 30 34 35 45 49 53 56"
for lb in $MIXES; do for a in $ARMS; do run $lb-arm$a-rep1 bash script/mix-20260911.sh $lb arm$a 1; done; push "$lb screened (x1)"; done
echo SCREENDONE $(date -Is)
for lb in $MIXES; do
  top=$(python3 - $lb <<'PY'
import re, sys, statistics as st
from pathlib import Path
M = Path('/home/oy/iCAT/result/mix-20260911'); lb = sys.argv[1]; w = {}
def tot(d):
    f = M / d / 'summary.txt'
    if not f.exists() or (M / d / 'SUSPECT.txt').exists(): return None
    m = re.search(r'^total .*WAF=([\d.]+)', f.read_text(), re.M); return float(m[1]) if m else None
for a in [46, 31, 32, 17, 16, 15, 30, 34, 35, 45, 49, 53, 56]:
    if (x := tot(f'{lb}-arm{a:02d}-rep1')): w[f'arm{a:02d}'] = x
for p, a in [('fixed47', 47), ('fixed50', 50), ('fixed37', 37)]:
    xs = [x for r in (1, 2, 3) if (x := tot(f'{lb}-{p}-rep{r}'))]
    if xs: w[p] = st.mean(xs)
print(' '.join(sorted(w, key=w.get)[:3]))
PY
)
  echo "$lb top3 at x1: $top"
  for p in $top; do run $lb-$p-rep1-x3 env MULT=3 VM_RUN=900 bash script/mix-20260911.sh $lb $p 1; done; push "$lb confirmed (x3): $top"
done
python3 analysis/all-tables.py > /dev/null 2>&1; python3 analysis/figures.py > /dev/null 2>&1; python3 analysis/v4-vs-cat.py > /dev/null 2>&1; bash analysis/dashboard-build.sh > /dev/null 2>&1; push "tables and figures regenerated"
echo QUEUE31DONE $(date -Is)
