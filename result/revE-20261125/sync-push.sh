#!/usr/bin/env bash
# revE-20261125: copy a finished run (reduced: no kernel-snapshots) and campaign logs into the report worktree, run the
# pre-registered analysis, commit and push branch report/data-validity-20261124. Runs only between measurements.
C=/home/oy/iCAT/result/revE-20261125; W=/home/oy/iCAT-final; R=$W/result/revE-20261125; run=${1:-}
exec 7>$C/git.lock; flock 7
mkdir -p $R/raw $R/console
[[ -n "$run" && -d $C/raw/$run ]] && rsync -a --exclude kernel-snapshots $C/raw/$run/ $R/raw/$run/
rsync -a $C/console/ $R/console/
cp -p $C/{preregistration.md,window_plan.md,modules.sha256,queue-order.registered.txt,queue.log,runs.tsv,checks.tsv,loadsampler.tsv,runner-revE.sh,port.diff,run-one.sh,safety-env.sh,queue-revE.sh,check-run.py,sync-push.sh,loadsampler.sh} $R/ 2>/dev/null

mkdir -p $R/build && cp -p $C/build/* $R/build/ 2>/dev/null
cd $W
python3 -I analysis/revision_gocom/revE_analyze.py $C/raw > /dev/null 2>&1 || echo "analysis failed" >> $C/queue.log
git add result/revE-20261125 result/revE-20261125-analysis >/dev/null 2>&1
git -c user.name=oyeong011 -c user.email=oyeong011@gmail.com commit -q -m "revE-20261125: ${run:-campaign logs} (GoCom, auto)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" >/dev/null 2>&1
git push -q origin report/data-validity-20261124 >/dev/null 2>&1 && echo "$(date -Is) pushed ${run:-logs}" >> $C/queue.log || echo "$(date -Is) push FAILED ${run:-logs} (not an experiment anomaly; runs continue)" >> $C/queue.log
