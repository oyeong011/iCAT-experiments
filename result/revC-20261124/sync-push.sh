#!/usr/bin/env bash
# revC-20261124: copy a finished run (reduced: no kernel-snapshots) and campaign logs into the report worktree, run the
# pre-registered analysis, commit and push branch report/data-validity-20261124. Runs only between measurements.
C=/home/oy/iCAT/result/revC-20261124; W=/home/oy/iCAT-final; R=$W/result/revC-20261124; run=${1:-}
exec 7>$C/git.lock; flock 7
mkdir -p $R/raw $R/console
[[ -n "$run" && -d $C/raw/$run ]] && rsync -a --exclude kernel-snapshots $C/raw/$run/ $R/raw/$run/
rsync -a $C/console/ $R/console/
cp -p $C/{preregistration.md,concurrency_check.md,modules.sha256,queue-order.registered.txt,queue.log,runs.tsv,checks.tsv,loadsampler.tsv,runner-revC.sh,run-one.sh,safety-env.sh,queue.sh,queue-main.sh,check-run.py,sync-push.sh,loadsampler.sh} $R/ 2>/dev/null
[[ -f $C/queue-main.log ]] && cp -p $C/queue-main.log $R/
mkdir -p $R/build && cp -p $C/build/*.log $R/build/ 2>/dev/null
cd $W
python3 -I analysis/revision_gocom/revC_analyze.py $C/raw > /dev/null 2>&1 || echo "analysis failed" >> $C/queue-main.log
git add result/revC-20261124 result/revC-20261124-analysis >/dev/null 2>&1
git -c user.name=oyeong011 -c user.email=oyeong011@gmail.com commit -q -m "revC-20261124: ${run:-campaign logs} (GoCom, auto)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" >/dev/null 2>&1
git push -q origin report/data-validity-20261124 >/dev/null 2>&1 && echo "$(date -Is) pushed ${run:-logs}" >> $C/queue-main.log || echo "$(date -Is) push FAILED ${run:-logs} (not an experiment anomaly; runs continue)" >> $C/queue-main.log
