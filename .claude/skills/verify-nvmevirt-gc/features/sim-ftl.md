# Userspace FTL run

The userspace driver feeds NVMe write and read commands straight into the real FTL code of a module source copy, fills the device once, overwrites it several times, and checks mapping, line, and GC-buffer invariants. It ends with one `sim` line holding the page counts and `invariants=ok`.

## Sub-features

- `sim-greedy` runs the Greedy policy.
- `sim-arm` runs one fixed CAT arm, `arm00` to `arm59`.
- `sim-smartgc` runs SmartGC with its default parameters (Q-table starts at zero).
- `sim-smartgc-options` runs SmartGC with changed parameters: `alpha`, `gamma`, `eps_start`, `eps_min`, `w`, `gcbuf` (all per mille), `eps_halflife`, `batch`, `q_init`, `seed`, `eq8` (0 = ranked list, 1 = Eq. 8 per line).
- `sim-workload` switches the write pattern with `workload=zones` (default) or `workload=uniform`.
- `sim-reject` refuses an unknown policy or option with a non-zero exit.

## How to get to it (user POV)

- Run `bash smartgc-src/test/run.sh <policy> [options]` in Linux or WSL.
- Run `bash .claude/skills/verify-nvmevirt-gc/verify.sh sim <run-id> <name> <policy> [options]` to get the same run with an evidence file.

## Driving it with verify.sh

Preconditions:

- `bash $V doctor` reports `sim: ready`.
- No file `result/<run-id>/<name>.log` exists yet.

- **Greedy.** Run `bash $V sim <run-id> greedy greedy capacity_mib=8192 overwrite_x=6`. The command prints `PASS` with a `sim policy=greedy ... invariants=ok` line.
- **Fixed CAT.** Run `bash $V sim <run-id> arm47 arm47 capacity_mib=8192 overwrite_x=6`. The command prints `PASS` with a `sim policy=cat-fig7-fixed ... invariants=ok` line.
- **SmartGC default.** Run `bash $V sim <run-id> smartgc-default smartgc capacity_mib=8192 overwrite_x=6`. The command prints `PASS`. The log has four `smartgc part=N steps=...` lines with `steps` above zero and four `wear part=N` lines.
- **SmartGC options.** Run `bash $V sim <run-id> smartgc-qinit2000 smartgc capacity_mib=8192 overwrite_x=6 q_init=2000`. The command prints `PASS`. With the ranked rule the line reads `host_pages=11759730 gc_pages=72537784` (unchanged from commit ec113bb29 through the 2026-11-19 edits).
- **GC buffer off and on.** Run the SmartGC drive with `gcbuf=0` and with `gcbuf=50`. With `gcbuf=0` every `smartgc part=` line shows `absorbed=0 frozen=0`. With `gcbuf=50` `absorbed` is above zero and `waf_nand` is below `waf`.
- **Uniform workload.** Add `workload=uniform` to any drive. The `sim` line shows `workload=uniform`.
- **Rejection.** Run `bash $V sim <run-id> neg-unknown-policy nosuch`. The command prints `FAIL ... no-exit=0 no-invariants=ok` and exits 1. The log ends with `exit=2`.
- **Proof.** Run `bash $V check result/<run-id>/*.log`. Every intended drive prints `PASS`, and the rejection drive prints `FAIL`.

## Gotchas

- The driver is deterministic. The same source, policy and options give the same page counts. A different count means the code or the options changed.
- `waf` is `1 + gc_pages/host_pages`. `waf_nand` subtracts writes the GC buffer absorbed. Neither is a measurement.
- Fixed CAT depends on page age, and the driver uses a fake clock. Its WAF says little about the real device.
- `run.sh` knows only `smartgc`, `greedy` and `armNN`. The online learner (policy 2 in the `online-*-src` copies) has no userspace drive.
- Each log starts with two `-Wmaybe-uninitialized` compiler warnings from `ssd.c`. They are in the original source.
- SmartGC with the default `q_init=0` gives a WAF near 12.8 on the standard workload, against 7.2 for Greedy. That is recorded behavior of the zero-initialised Q-table with the ranked rule, not a harness fault. See `smartgc-src/SMARTGC.md` and [the selection rule](./sim-selection-rule.md).
- In the proc output the `smartgc part=` lines come before the `wear part=` lines.
