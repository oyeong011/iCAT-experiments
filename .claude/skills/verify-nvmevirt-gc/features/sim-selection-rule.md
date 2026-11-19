# SmartGC victim selection rule

SmartGC builds its victim list with one of two rules. The default ranks eligible lines by Q(s, erase) and takes `batch` of them. `eq8=1` reads Eq. 8 of the paper literally: every eligible line picks its own action, and all lines that picked erase form the list. The `smartgc part=` lines show which rule ran through the list length.

## Sub-features

- `rule-ranked` runs the default rule: lists of `batch` lines (8 unless changed).
- `rule-eq8` runs the per-line rule: lists as long as the number of lines that chose erase.
- `rule-eq8-fallback` keeps GC going when no line chose erase, by listing one random eligible line.
- `rule-listed` reports `listed=` on each `smartgc part=` line, the running count of lines put on a list.

## How to get to it (user POV)

- Userspace driver: add `eq8=1` to a `smartgc` run.
- Kernel module: load with `smartgc_eq8=1`. It is read-only after load and printed as `eq8=` on the `SmartGC init` kernel-log line.

## Driving it with verify.sh

Preconditions:

- `bash $V doctor` reports `sim: ready`.
- No file `result/<run-id>/<name>.log` exists yet.

- **Ranked rule.** Run `bash $V sim <run-id> rank-default smartgc capacity_mib=8192 overwrite_x=6`. It prints `PASS`. On each `smartgc part=N` line `listed` divided by `steps` is 8.0.
- **Eq. 8 rule.** Run `bash $V sim <run-id> eq8-default smartgc capacity_mib=8192 overwrite_x=6 eq8=1`. It prints `PASS`. `listed` divided by `steps` is far above 8 (about 1100 on the standard workload), and `steps` is in the hundreds per partition.
- **Fallback.** Run `bash $V sim <run-id> eq8-eps0 smartgc capacity_mib=8192 overwrite_x=6 eq8=1 eps_start=0 eps_min=0`. It prints `PASS` with `eps_permille=0` and `explored` above zero. With no exploration, `explored` counts only the fallback picks.
- **Repeat check.** Run `bash $V same result/<run-id>/eq8-default.log result/smartgc-eq8-20261119/eq8-default.log` on unchanged sources. It prints `SAME host_pages=11759730 gc_pages=96454024`.
- **Ranked rule unchanged.** Run `bash $V same result/<run-id>/rank-default.log result/smartgc-eq8-20261119/rank-default.log`. It prints `SAME host_pages=11759730 gc_pages=139087054`.
- **Proof.** The evidence logs, the two `SAME` lines, and `listed`/`steps` read from the `smartgc part=` lines.

## Gotchas

- Under `eq8=1` a step is hundreds to thousands of erases, so the default epsilon half-life of 2048 steps is never reached and epsilon stays at its start value. On the standard workload 86% of the victims are then random picks. Compare rules only with the epsilon settings stated.
- `batch` has no effect under `eq8=1`.
- Ties between Q(s, keep) and Q(s, erase) go to keep, and the list is erased from the largest Q(s, erase) down. Neither is fixed by the paper.
- `script/mix-gc-20261010.sh` passes a fixed `insmod` argument list, so a kernel run cannot switch on `smartgc_eq8` without a script change.
- WAF differences between the rules come from the userspace driver and are checks of logic, not measurements. The recorded comparison is run `smartgc-eq8-20261119` in `EXPERIMENT_LOG.md`.
