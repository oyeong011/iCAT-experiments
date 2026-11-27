#!/usr/bin/env bash
# revF-20261127: copy a finished run (reduced: no kernel-snapshots) and campaign logs into the report worktree, commit and push
# branch report/data-validity-20261124. Runs only between measurements. No analysis here (n=1 per policy; analysed after the batch).
C=/home/oy/iCAT/result/revF-20261127; W=/home/oy/iCAT-final; R=$W/result/revF-20261127; run=${1:-}
exec 7>/home/oy/iCAT/result/revE-20261125/git.lock; flock 7
mkdir -p $R/raw $R/console $R/build $R/inputs
[[ -n "$run" && -d $C/raw/$run ]] && rsync -a --exclude kernel-snapshots $C/raw/$run/ $R/raw/$run/
rsync -a $C/console/ $R/console/; rsync -a $C/build/ $R/build/; rsync -a $C/inputs/ $R/inputs/
cp -p $C/{preregistration.md,modules.sha256,queue-order.registered.txt,queue.log,runs.tsv,checks.tsv,loadsampler.tsv,runner-revF.sh,port.diff,run-one.sh,safety-env.sh,queue-revF.sh,queue-revF-resume.sh,check-run.v1-falsepositive.py,check-run.py,sync-push.sh,loadsampler.sh,journal.md} $R/ 2>/dev/null
cd $W
git add result/revF-20261127 >/dev/null 2>&1
git -c user.name=oyeong011 -c user.email=oyeong011@gmail.com commit -q -m "revF-20261127: ${run:-campaign logs} (GoCom, auto)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" >/dev/null 2>&1
git push -q origin report/data-validity-20261124 >/dev/null 2>&1 && echo "$(date -Is) pushed ${run:-logs}" >> $C/queue.log || echo "$(date -Is) push FAILED ${run:-logs} (not an experiment anomaly; runs continue)" >> $C/queue.log
