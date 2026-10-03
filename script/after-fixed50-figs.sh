#!/usr/bin/env bash
# 10-04: when the OLTP->Varmail 10 h CAT-50 run ends, redraw Fig.6 / Fig.7 (10 h) with it and push.
# Command line deliberately contains no runner name (queues' busy check is pgrep -f on the runner path).
cd /home/oy/iCAT
D=result/mix-20260911/mixO-fixed50-rep1-x20
until [[ -e $D/summary.txt ]] || grep -q 'exit=' $D.console.txt 2>/dev/null; do sleep 120; done
sleep 180   # let the queue finish its own commit/push first
python3 analysis/fig6-10h.py && python3 analysis/fig7-10h.py
for i in 1 2 3 4 5; do
  git add analysis figs && git commit -qm "Fig.6/Fig.7 (10 h) redrawn with CAT-50 robust ($(grep -o '^total .*WAF=[0-9.]*' $D/summary.txt 2>/dev/null | grep -o 'WAF=.*' || echo 'run failed'))" && git push -q && break
  sleep 60
done
echo "AFTER50DONE $(date -Is)"
