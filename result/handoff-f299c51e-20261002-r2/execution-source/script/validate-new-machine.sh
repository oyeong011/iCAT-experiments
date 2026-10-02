#!/usr/bin/env bash
# Original 3-region writes, 600 seconds each; WAF must be within 1% per arm.
set -Eeuo pipefail
cd /home/oy/iCAT
source script/env.sh
grep -Fq 'memmap=8G$4G' /proc/cmdline || { echo 'BLOCKED: memory reservation missing'; exit 2; }
sudo -n true || { echo 'BLOCKED: administrator setup missing'; exit 2; }
o="result/validate-$(hostname)-$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$o"
echo "Evidence: $o"
for t in arm47 arm50 gh-greedy; do
    [[ -f "buildoutput/nvmev-$t.ko" ]] || { echo "BLOCKED: missing module $t"; exit 2; }
done
for t in arm47 arm50 gh-greedy; do
    status=0
    GH_TEST_JOB=gh-test4.fio bash script/gh-fio.sh "$t" > "$o/$t.console.txt" 2>&1 || status=$?
    printf '%s\n' "$status" > "$o/$t.exit-code.txt"
done
python3 - "$o" <<'CHECK' | tee "$o/summary.txt"
import re, sys, pathlib
root = pathlib.Path(sys.argv[1])
ref = {'arm47': 1.7455, 'arm50': 1.7859, 'gh-greedy': 2.186}
ok = True
for tag, baseline in ref.items():
    console = (root / f'{tag}.console.txt').read_text(errors='replace')
    status = int((root / f'{tag}.exit-code.txt').read_text())
    match = re.search(r'^\[RESULT\] (\S+)', console, re.M)
    stats = []
    if match and pathlib.Path(match[1]).is_file():
        stats = re.findall(r'GC stats: .*?host_pages=(\d+) gc_pages=(\d+)', pathlib.Path(match[1]).read_text(errors='replace'))
    waf = 1 + int(stats[-1][1]) / int(stats[-1][0]) if stats and int(stats[-1][0]) > 0 else None
    diff = (waf / baseline - 1) * 100 if waf is not None else None
    passed = status == 0 and diff is not None and abs(diff) <= 1
    ok &= passed
    print(f'{tag}: exit={status}, reference={baseline}, WAF={waf}, difference_percent={diff}, {"PASS" if passed else "FAIL"}')
print('PASS' if ok else 'FAIL: do not mix results with original machine')
sys.exit(0 if ok else 1)
CHECK
