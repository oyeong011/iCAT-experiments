#!/usr/bin/env bash
# Verification helper for the NVMeVirt GC policies in this repo (see SKILL.md next to this file).
# Runs inside Linux or WSL, from any directory. Evidence goes to result/<run-id>/ and is never overwritten.
#   verify.sh doctor                                       read-only: is this checkout and host worth driving?
#   verify.sh sim <run-id> <name> <policy> [sim options]   one userspace FTL run -> result/<run-id>/<name>.log
#   verify.sh kbuild <run-id> <tag> <src dir> [make vars]  compile one module copy -> result/<run-id>/kbuild-<tag>.log
#   verify.sh check <log>...                               pass/fail of sim logs
#   verify.sh same <log A> <log B>                         two sim logs moved the same host and GC pages
# sim: policy is smartgc, greedy or arm00..arm59; SIM_SRC=<dir> picks the module source copy (default smartgc-src).
# kbuild: KDIR=<kernel build dir> (default /lib/modules/$(uname -r)/build).
set -Eeuo pipefail
root=$(readlink -f "$(dirname "$(readlink -f "$0")")/../../..")
cd "$root"
die() { echo "verify: $*" >&2; exit 2; }
rundir() { [[ $1 =~ ^[A-Za-z0-9._-]+$ ]] || die "bad run id $1"; mkdir -p "result/$1"; echo "result/$1"; }
stamp() { # stamp <source dir>: what was run, for the evidence file
    echo "# host $(hostname) $(uname -sr) gcc $(gcc -dumpfullversion)"
    # fileMode/autocrlf: a Windows checkout read from WSL otherwise shows every file as modified
    echo "# git $(git rev-parse HEAD 2>/dev/null || echo unavailable) changed-files-under-$1: $(git -c core.fileMode=false -c core.autocrlf=true status --porcelain -- "$1" 2>/dev/null | wc -l)"
    sha256sum "$1"/conv_ftl.c "$1"/conv_ftl.h "$1"/ssd.c "$1"/pqueue/pqueue.c "$1"/Kbuild smartgc-src/test/sim.c smartgc-src/test/kshim.h | sed 's/^/# sha256 /'
}
simline() { grep -m1 '^sim ' "$1" || true; }
check_one() {
    local f=$1 why=
    grep -q '^exit=0$' "$f" || why="$why no-exit=0"
    grep -q '^sim .* invariants=ok$' "$f" || why="$why no-invariants=ok"
    ! grep -q 'BUG at\|INVARIANT FAILED' "$f" || why="$why BUG-or-INVARIANT-FAILED"
    if [[ -z $why ]]; then echo "PASS $f: $(simline "$f")"; else echo "FAIL $f:$why"; return 1; fi
}
key() { simline "$1" | tr ' ' '\n' | grep -E '^(host_pages|gc_pages)=' | tr '\n' ' '; }

case ${1:-} in
doctor)
    rc=0
    echo "repo: $root"
    echo "host: $(hostname) $(uname -sr)"
    for f in smartgc-src/test/run.sh smartgc-src/test/sim.c smartgc-src/conv_ftl.c AGENTS.md EXPERIMENT_LOG.md; do
        [[ -e $f ]] || { echo "MISSING $f"; rc=1; }
    done
    if command -v gcc >/dev/null; then echo "sim: ready (gcc $(gcc -dumpfullversion))"; else echo "sim: NOT ready (no gcc)"; rc=1; fi
    K=${KDIR:-/lib/modules/$(uname -r)/build}
    if [[ -f $K/Makefile ]]; then echo "kbuild: ready (KDIR=$K)"; else echo "kbuild: NOT ready (no kernel build dir at $K; set KDIR)"; fi
    if [[ $(uname -r) == *microsoft* ]]; then
        echo "kernel run: NOT possible here (WSL kernel; modules are built for the experiment kernel)"
    else
        echo "kernel run: host kernel $(uname -r); modules for it: $(ls buildoutput/build-manifest-"$(uname -r)".tsv 2>/dev/null || echo none built)"
        if lsmod | grep -q '^nvmev '; then echo "  nvmev is LOADED: an experiment may be running, do not drive the device"; rc=1; else echo "  nvmev not loaded"; fi
        l=result/mix-20260911/device.lock
        if [[ -e $l ]] && ! flock -n "$l" true; then echo "  device.lock is HELD: an experiment is running"; rc=1; fi
        pgrep -a 'fio|filebench' | sed 's/^/  running: /' || true
    fi
    exit $rc;;
sim)
    (($# >= 4)) || die "usage: verify.sh sim <run-id> <name> <policy> [sim options]"
    d=$(rundir "$2"); name=$3; policy=$4; shift 4
    log=$d/$name.log; [[ ! -e $log ]] || die "refusing to overwrite $log"
    src=${SIM_SRC:-smartgc-src}; [[ -f $src/conv_ftl.c ]] || die "no module source at $src"
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    {
        echo "# started $(date -Is) SIM_SRC=$src policy=$policy options: $*"
        stamp "$src"
        rc=0; SIM_SRC=$src SIM_OUT=$tmp bash smartgc-src/test/run.sh "$policy" "$@" || rc=$?
        echo "exit=$rc"; echo "# finished $(date -Is)"
    } > "$log" 2>&1
    check_one "$log";;
kbuild)
    (($# >= 4)) || die "usage: verify.sh kbuild <run-id> <tag> <src dir> [make vars]"
    d=$(rundir "$2"); tag=$3; src=$4; shift 4
    K=${KDIR:-/lib/modules/$(uname -r)/build}; [[ -f $K/Makefile ]] || die "no kernel build dir at $K (set KDIR)"
    log=$d/kbuild-$tag.log; [[ ! -e $log ]] || die "refusing to overwrite $log"
    [[ -f $src/Kbuild ]] || die "no module source at $src"
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    cp -r "$src" "$tmp/src"
    rc=0
    {
        echo "# started $(date -Is) src=$src KDIR=$K make vars: $*"
        stamp "$src"
        make -C "$K" M="$tmp/src" clean >/dev/null 2>&1 || true
        make -C "$K" M="$tmp/src" -j"$(nproc)" "$@" modules || rc=$?
        echo "exit=$rc"
        if ((rc == 0)); then
            echo "module sha256 $(sha256sum < "$tmp/src/nvmev.ko" | cut -c1-64)"
            strings "$tmp/src/nvmev.ko" | grep '^parm=' | sort | sed 's/^/module /'
        fi
        echo "# finished $(date -Is)"
    } > "$log" 2>&1
    echo "$([[ $rc == 0 ]] && echo PASS || echo FAIL) $log: exit=$rc warnings=$(grep -c 'warning:' "$log" || true) params=$(grep -c '^module parm=' "$log" || true)"
    grep 'warning:' "$log" | sed 's/^.*warning: //' | sort | uniq -c || true
    exit $rc;;
check)
    shift; (($# >= 1)) || die "usage: verify.sh check <log>..."
    rc=0; for f in "$@"; do check_one "$f" || rc=1; done; exit $rc;;
same)
    (($# == 3)) || die "usage: verify.sh same <log A> <log B>"
    a=$(key "$2"); b=$(key "$3")
    [[ -n $a && -n $b ]] || die "no sim line in one of the logs"
    if [[ $a == "$b" ]]; then echo "SAME $a"; else echo "DIFFERENT  $2: $a  $3: $b"; exit 1; fi;;
*) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 2;;
esac
