#!/usr/bin/env bash
# One-screen progress report. Usage: bash script/status.sh
cd /home/oy/iCAT
B=/tmp/claude-1000/-home-oy-nvmevirt/644aa240-1852-482e-a060-ce2cfc119144/scratchpad
echo "== $(date '+%m-%d %H:%M')  지금 도는 run:"
pgrep -af "script/(gh-fio|gh-filebench|sqlite|mix-20260911)\.sh" | grep -v pgrep | sed 's/^[0-9]* bash //' | head -2
echo "== 대기 중인 큐:"; pgrep -af "gh-queue|sweep-2026" | grep -v pgrep | sed 's/^[0-9]* bash script\///'
echo "== sweep(60 arm): test4 $(ls result/sweep-20260915/test4-arm*.console.txt 2>/dev/null | wc -l)/60  sqlite-a $(ls result/sqlite/a-arm*.console.txt 2>/dev/null | wc -l)/60  oltp $(ls result/filebench/oltp-arm*.console.txt 2>/dev/null | wc -l)/60"
echo "== mix(v1): $(ls -d result/mix-20260911/mix?-*-rep[123] 2>/dev/null | wc -l)/252 run   v2: $(ls -d result/mix-20260911/*onlinev2* 2>/dev/null | grep -vc smoke)"
echo "== 실패: $(cat $B/sweep.out $B/queue6.out $B/queue7.out $B/queue8.out 2>/dev/null | grep -c FAIL)"
echo "== 마지막 push: $(git log -1 --format='%ci %s' | cut -c1-70)"
