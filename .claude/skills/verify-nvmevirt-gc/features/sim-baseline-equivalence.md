# Unchanged baseline policies

`smartgc-src` is a copy of `varmail-compare-src` with SmartGC added. Greedy and fixed CAT built from `smartgc-src` must make the same GC decisions as before, so that `sg-greedy` and `sg-arm47` can stand in for the old modules while adding the erase-wear report.

## Sub-features

- `base-greedy` compares Greedy between the two source copies.
- `base-arm` compares one fixed CAT arm between the two source copies.
- `base-repeat` compares a drive with an earlier log of the same source and options.

## How to get to it (user POV)

- Run the userspace driver twice with the same policy and options, once per source copy, and compare the page counts on the two `sim` lines.

## Driving it with verify.sh

Preconditions:

- `bash $V doctor` reports `sim: ready`.
- Both `smartgc-src/` and `varmail-compare-src/` exist.

- **Greedy, new copy.** Run `bash $V sim <run-id> greedy-new greedy capacity_mib=8192 overwrite_x=6`. It prints `PASS`.
- **Greedy, old copy.** Run `env SIM_SRC=varmail-compare-src bash $V sim <run-id> greedy-old greedy capacity_mib=8192 overwrite_x=6`. It prints `PASS`, and the log header shows `SIM_SRC=varmail-compare-src`.
- **Compare Greedy.** Run `bash $V same result/<run-id>/greedy-new.log result/<run-id>/greedy-old.log`. It prints `SAME host_pages=... gc_pages=...` and exits 0.
- **Fixed CAT.** Repeat the three steps with policy `arm47` and names `arm47-new` and `arm47-old`. `same` prints `SAME`.
- **Repeat check.** Run `bash $V same result/<run-id>/<name>.log result/smartgc-dev-20261114/s5-final-smartgc-qinit2000.log` after a `smartgc ... q_init=2000` drive on unchanged sources. It prints `SAME host_pages=11759730 gc_pages=72537784`.
- **Proof.** The two evidence logs and the `SAME` line, copied into the `EXPERIMENT_LOG.md` entry.

## Gotchas

- `same` compares only `host_pages` and `gc_pages`. The old copy prints no `wear` lines, so a full-file diff always differs.
- A `DIFFERENT` result after an edit to shared code (`ssd.c`, the write path in `conv_ftl.c`) is a real regression for the baselines until explained.
- `SIM_SRC` must be set with `env` when calling through `wsl.exe`.
- Equal page counts in the fake-clock driver are a check of logic. They do not prove equal timing in the kernel.
