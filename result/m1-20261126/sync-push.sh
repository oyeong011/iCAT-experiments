#!/usr/bin/env bash
# m1-20261126: copy a finished run into the report worktree (no kernel-snapshots; kernel logs reduced: the emulator channel-model
# warning "Need to increase array size" lines are counted and dropped, the rest is kept gzip'd), commit and push the report branch.
# Uses the same git lock as revE (fd 7). Runs only between measurements.
C=/home/oy/iCAT/result/m1-20261126; W=/home/oy/iCAT-final; R=$W/result/m1-20261126; run=${1:-}
exec 7>/home/oy/iCAT/result/revE-20261125/git.lock; flock 7
mkdir -p $R/raw $R/sampler $R/console
if [[ -n "$run" && -d $C/raw/$run ]]; then
  rsync -a --exclude kernel-snapshots --exclude kernel.log --exclude kernel-final.log $C/raw/$run/ $R/raw/$run/
  for k in kernel.log kernel-final.log; do [[ -f $C/raw/$run/$k ]] || continue
    printf '%s chmodel_warn_lines=%s\n' "$k" "$(grep -c 'Need to increase array size' $C/raw/$run/$k)" >> $R/raw/$run/kernel-reduced.txt
    grep -v 'Need to increase array size' $C/raw/$run/$k | gzip -9 > $R/raw/$run/$k.nowarn.gz; done
  [[ -d $C/sampler/$run ]] && rsync -a $C/sampler/$run/ $R/sampler/$run/
fi
rsync -a $C/console/ $R/console/ 2>/dev/null
cp -p $C/{preregistration.md,modules.sha256,queue-order.registered.txt,queue.log,checks.tsv,runner-m1.sh,queue-m1.sh,check-m1.py,sync-push.sh,sampler.sh,bench-sim.sh} $R/ 2>/dev/null
mkdir -p $R/build $R/tools $R/sim && cp -p $C/build/*.diff $C/build/*.log $R/build/ 2>/dev/null; cp -p $C/tools/* $R/tools/; rsync -a --exclude '*.o' $C/sim/ $R/sim/
cd $W
git add result/m1-20261126 >/dev/null 2>&1
git -c user.name=oyeong011 -c user.email=oyeong011@gmail.com commit -q -m "m1-20261126: ${run:-campaign logs} (GoCom, auto)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" >/dev/null 2>&1
git push -q origin report/data-validity-20261124 >/dev/null 2>&1 && echo "$(date -Is) pushed ${run:-logs}" >> $C/queue.log || echo "$(date -Is) push FAILED ${run:-logs} (not an experiment anomaly)" >> $C/queue.log
