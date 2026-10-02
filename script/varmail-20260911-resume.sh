#!/usr/bin/env bash
# Post-reboot driver for the varmail comparison: verify both module kinds, then
# smoke and main per policy, one at a time. Stops at the first failure and
# reaps a stuck barrier subshell (it would otherwise hold the flock fds).
set -Eeuo pipefail
root=/home/oy/iCAT
out="$root/result/varmail-20260911"
cd "$root"
step() { echo "[$(date -Is)] $*"; }
reap() {
    if pgrep -f 'varmail-20260908.sh barrier' >/dev/null; then
        step "stuck barrier subshell found; killing"
        pkill -f 'varmail-20260908.sh barrier' || true
    fi
    [[ ! -e /sys/module/nvmev ]] || { step "nvmev still loaded"; exit 1; }
}
[[ ! -e /sys/module/nvmev ]] || { echo "nvmev loaded; reboot first"; exit 1; }
sha256sum --check --status result/varmail-20260908/run-inputs.sha256
if [[ ! -e result/measurement-control-20260907/varmail-fixed47-k31b ]]; then
    step verify fixed47
    MEASUREMENT_AGE_DESCRIPTION=LAST_INVALIDATION bash script/verify-measurement-20260907.sh varmail-20260908-fixed47 varmail-fixed47-k31b > "$out/verify-fixed47-k31b.console.txt" 2>&1
fi
if [[ ! -e result/measurement-control-20260907/online-k31b ]]; then
    step verify online
    MEASUREMENT_AGE_DESCRIPTION=LAST_INVALIDATION bash script/verify-measurement-20260907.sh online-mix-20260907 online-k31b > "$out/verify-online-k31b.console.txt" 2>&1
fi
for mode in smoke main; do
    for policy in fixed47 online fixed37; do
        dir="result/varmail-20260908/$mode-$policy"
        if [[ -e "$dir/exit-code.txt" ]] && [[ $(< "$dir/exit-code.txt") == 0 ]]; then step "skip $mode $policy (done)"; continue; fi
        [[ ! -e "$dir" ]] || { step "$dir exists with non-zero/no exit code; inspect"; exit 1; }
        step "$mode $policy"
        bash script/varmail-20260908.sh "$mode" "$policy" > "result/varmail-20260908/$mode-$policy.console.txt" 2>&1 || { step "FAIL $mode $policy"; reap; exit 1; }
        [[ ! -e "$dir/barrier-failed.txt" ]] || { step "barrier failed"; reap; exit 1; }
        reap
        cat "$dir/summary.txt"
    done
done
step ALL DONE
